// Copyright Advanced Micro Devices, Inc., or its affiliates.
// SPDX-License-Identifier: MIT

#include <origami/simulator/tensilelite/formocast_simulator.hpp>

#include <Tensile/Utils.hpp>
#include "SolutionIterator.hpp"
#include <Tensile/ContractionProblem.hpp>
#include <Tensile/ContractionSolution.hpp>
#include <Tensile/MasterSolutionLibrary.hpp>
#include <Tensile/Predicates.hpp>
#include <Tensile/hip/HipHardware.hpp>

#include <algorithm>
#include <array>
#include <charconv>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace
{
    using origami::Formocast;

    // This adapter's native validity boundary is the real protected runtime
    // checkSolution implementation.  Formal construction supplies real solution,
    // problem, library, and hardware objects before this method can be invoked.
    class ActualCheckSolutionAdapter final : public TensileLite::Client::SolutionIterator
    {
    public:
        ActualCheckSolutionAdapter(
            std::shared_ptr<TensileLite::MasterSolutionLibrary<TensileLite::ContractionProblemGemm>> library,
            std::shared_ptr<TensileLite::Hardware> hardware)
            : SolutionIterator(std::move(library), std::move(hardware), false)
        {
        }

        bool checkActual(TensileLite::ContractionSolution& solution,
                         TensileLite::ContractionProblemGemm& problem)
        {
            return SolutionIterator::checkSolution(solution, problem, false);
        }

        bool moreSolutionsInProblem() const override
        {
            return false;
        }

        std::shared_ptr<TensileLite::ContractionSolution> getSolution() override
        {
            return {};
        }

        void postProblem() override {}
        void preSolution(TensileLite::ContractionSolution* const) override {}
        void postSolution() override {}
    };

    struct Row
    {
        int ordinal;
        bool checkSolution;
        int M;
        int N;
        int batches;
        int K;
        Formocast::SizeMapping mapping;
        double microSeconds;
    };

    struct QueueResult
    {
        double threshold;
        bool predictionDisabled;
        std::vector<int> sortedOrdinals;
        std::vector<int> queuePrefix;
        int thresholdIndex;
        double thresholdValue;
    };

    int parseInteger(std::string_view token)
    {
        if(token.empty() || token.front() == '+' || (token.size() > 1 && token.front() == '0')
           || (token.size() > 2 && token[0] == '-' && token[1] == '0'))
            throw std::runtime_error("non-canonical integer token");
        int result = 0;
        auto [end, error] = std::from_chars(token.data(), token.data() + token.size(), result);
        if(error != std::errc{} || end != token.data() + token.size())
            throw std::runtime_error("invalid integer token");
        return result;
    }

    std::vector<std::string_view> splitStrict(std::string const& line)
    {
        if(line.empty() || line.front() == ' ' || line.back() == ' ' || line.find("  ") != std::string::npos)
            throw std::runtime_error("non-canonical ASCII spacing");
        std::vector<std::string_view> tokens;
        std::string_view view(line);
        while(!view.empty())
        {
            auto position = view.find(' ');
            tokens.push_back(view.substr(0, position));
            if(position == std::string_view::npos)
                break;
            view.remove_prefix(position + 1);
        }
        return tokens;
    }

    std::vector<std::string> readStrictLines(std::filesystem::path const& path)
    {
        std::ifstream input(path, std::ios::binary);
        if(!input)
            throw std::runtime_error("cannot open input");
        std::string bytes((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());
        if(bytes.empty() || bytes.back() != '\n' || bytes.find('\r') != std::string::npos
           || bytes.find('\t') != std::string::npos || bytes.find('\0') != std::string::npos)
            throw std::runtime_error("input is not canonical LF-terminated ASCII");
        bytes.pop_back();
        std::vector<std::string> lines;
        std::stringstream stream(bytes);
        std::string line;
        while(std::getline(stream, line))
            lines.push_back(line);
        return lines;
    }

    Row parseRow(std::string const& line)
    {
        auto tokens = splitStrict(line);
        if(tokens.size() != 40)
            throw std::runtime_error("fixture row must contain exactly 40 scalar fields");
        std::array<int, 40> values{};
        for(size_t index = 0; index < tokens.size(); ++index)
            values[index] = parseInteger(tokens[index]);
        if(values[1] != 0 && values[1] != 1)
            throw std::runtime_error("checkSolution must be 0 or 1");
        size_t cursor = 0;
        Row row{};
        row.ordinal       = values[cursor++];
        row.checkSolution = values[cursor++] == 1;
        row.M             = values[cursor++];
        row.N             = values[cursor++];
        row.batches       = values[cursor++];
        row.K             = values[cursor++];
        row.mapping.waveNum = values[cursor++];
        for(auto& value : row.mapping.macroTile)
            value = values[cursor++];
        for(auto& value : row.mapping.matrixInstruction)
            value = values[cursor++];
        row.mapping.grvwA = values[cursor++];
        row.mapping.grvwB = values[cursor++];
        row.mapping.gwvwC = values[cursor++];
        row.mapping.gwvwD = values[cursor++];
        row.mapping.depthU = values[cursor++];
        row.mapping.globalSplitU = values[cursor++];
        row.mapping.workGroupMapping = values[cursor++];
        row.mapping.globalAccumulation = values[cursor++];
        row.mapping.workGroupMappingXCC = values[cursor++];
        row.mapping.workGroupMappingXCCGroup = values[cursor++];
        row.mapping.globalSplitUCoalesced = values[cursor++] != 0;
        row.mapping.globalSplitUWorkGroupMappingRoundRobin = values[cursor++] != 0;
        row.mapping.CUOccupancy = values[cursor++];
        row.mapping.PrefetchGlobalRead = values[cursor++];
        row.mapping.MathClocksUnrolledLoop = values[cursor++];
        row.mapping.DirectToVgprA = values[cursor++] != 0;
        row.mapping.DirectToVgprB = values[cursor++] != 0;
        row.mapping.NumLoadsCoalescedA = values[cursor++];
        row.mapping.NumLoadsCoalescedB = values[cursor++];
        row.mapping.VectorWidthA = values[cursor++];
        row.mapping.VectorWidthB = values[cursor++];
        row.mapping.LocalSplitU = values[cursor++];
        row.mapping.DirectToLdsA = values[cursor++] != 0;
        row.mapping.DirectToLdsB = values[cursor++] != 0;
        for(auto& value : row.mapping.waveGroup)
            value = values[cursor++];
        if(cursor != values.size())
            throw std::runtime_error("internal fixture row parser mismatch");
        return row;
    }

    double predict(Row const& row)
    {
        Formocast::ProblemInfo problem{};
        problem.M            = row.M;
        problem.N            = row.N;
        problem.NumBatches   = row.batches;
        problem.K            = row.K;
        problem.bpeA         = 2;
        problem.bpeB         = 2;
        problem.bpeD         = 2;
        problem.bpeCompute   = 4;
        problem.transA       = false;
        problem.transB       = false;
        problem.swizzleTensorA = false;
        problem.swizzleTensorB = false;
        problem.dataType     = origami::data_type_t::BFloat16;
        Formocast formocast;
        formocast.setProblem(problem);
        formocast.setSolution(row.mapping);
        formocast.setHardware(origami::hardware_t::architecture_t::gfx942);
        auto prediction = formocast.predictedPerformance();
        if(!std::isfinite(prediction.microSeconds))
            throw std::runtime_error("native prediction is not finite");
        return prediction.microSeconds;
    }

    TensileLite::ContractionProblemGemm makeProblem(Row const& row)
    {
        auto problem = TensileLite::ContractionProblemGemm::GEMM_Strides(
            false,
            false,
            rocisa::DataType::BFloat16,
            rocisa::DataType::BFloat16,
            rocisa::DataType::BFloat16,
            rocisa::DataType::BFloat16,
            row.M,
            row.N,
            row.K,
            row.batches,
            row.M,
            row.M * row.K,
            row.K,
            row.K * row.N,
            row.M,
            row.M * row.N,
            row.M,
            row.M * row.N,
            0.0);
        problem.setComputeInputTypeA(rocisa::DataType::BFloat16);
        problem.setComputeInputTypeB(rocisa::DataType::BFloat16);
        problem.setAlphaType(rocisa::DataType::Float);
        problem.setBetaType(rocisa::DataType::Float);
        return problem;
    }

    std::shared_ptr<TensileLite::ContractionSolution> makeSolution(Row const& row)
    {
        auto solution = std::make_shared<TensileLite::ContractionSolution>();
        solution->index = row.ordinal;
        solution->libraryLogicIndex = row.ordinal;
        solution->requiredHostWorkspaceSizePerProblem = 0;
        auto& mapping = solution->sizeMapping;
        mapping.waveNum = row.mapping.waveNum;
        mapping.macroTile = TensileLite::dim3(
            row.mapping.macroTile[0], row.mapping.macroTile[1], row.mapping.macroTile[2]);
        std::copy(
            row.mapping.matrixInstruction.begin(),
            row.mapping.matrixInstruction.end(),
            mapping.matrixInstruction.begin());
        mapping.grvwA = row.mapping.grvwA;
        mapping.grvwB = row.mapping.grvwB;
        mapping.gwvwC = row.mapping.gwvwC;
        mapping.gwvwD = row.mapping.gwvwD;
        mapping.depthU = row.mapping.depthU;
        mapping.globalSplitU = row.mapping.globalSplitU;
        mapping.workGroupMapping = row.mapping.workGroupMapping;
        mapping.globalAccumulation = row.mapping.globalAccumulation;
        mapping.workGroupMappingXCC = row.mapping.workGroupMappingXCC;
        mapping.workGroupMappingXCCGroup = row.mapping.workGroupMappingXCCGroup;
        mapping.globalSplitUCoalesced = row.mapping.globalSplitUCoalesced;
        mapping.globalSplitUWorkGroupMappingRoundRobin
            = row.mapping.globalSplitUWorkGroupMappingRoundRobin;
        mapping.CUOccupancy = row.mapping.CUOccupancy;
        mapping.PrefetchGlobalRead = row.mapping.PrefetchGlobalRead;
        mapping.MathClocksUnrolledLoop = row.mapping.MathClocksUnrolledLoop;
        mapping.DirectToVgprA = row.mapping.DirectToVgprA;
        mapping.DirectToVgprB = row.mapping.DirectToVgprB;
        mapping.NumLoadsCoalescedA = row.mapping.NumLoadsCoalescedA;
        mapping.NumLoadsCoalescedB = row.mapping.NumLoadsCoalescedB;
        mapping.VectorWidthA = row.mapping.VectorWidthA;
        mapping.VectorWidthB = row.mapping.VectorWidthB;
        mapping.LocalSplitU = row.mapping.LocalSplitU;
        mapping.DirectToLdsA = row.mapping.DirectToLdsA;
        mapping.DirectToLdsB = row.mapping.DirectToLdsB;
        std::copy(row.mapping.waveGroup.begin(), row.mapping.waveGroup.end(), mapping.waveGroup.begin());
        if(!row.checkSolution)
        {
            solution->problemPredicate = std::make_shared<
                TensileLite::Predicates::False<TensileLite::ContractionProblemGemm>>();
        }
        return solution;
    }

    std::shared_ptr<TensileLite::hip::HipAMDGPU> makeHardware()
    {
        auto hardware = std::make_shared<TensileLite::hip::HipAMDGPU>();
        hardware->processor = TensileLite::AMDGPU::Processor::gfx942;
        hardware->computeUnitCount = 304;
        hardware->deviceName = "s10r4-fixture-gfx942";
        auto analytical = origami::hardware_t::get_hardware_for_arch(
            origami::hardware_t::architecture_t::gfx942,
            304,
            65536,
            16 * 1024 * 1024,
            1700000);
        hardware->analyticalHardware = std::make_shared<origami::hardware_t>(analytical);
        return hardware;
    }

    std::vector<int> actualQueue(
        double threshold,
        std::shared_ptr<TensileLite::MasterSolutionLibrary<TensileLite::ContractionProblemGemm>> const& library,
        std::shared_ptr<TensileLite::Hardware> const& hardware,
        TensileLite::ContractionProblemGemm& problem)
    {
        TensileLite::Client::AllSolutionsIterator iterator(
            library, hardware, threshold, 0, 4, false);
        iterator.preProblem(&problem);
        std::vector<int> result;
        while(iterator.moreSolutionsInProblem())
        {
            auto solution = iterator.getSolution();
            if(!solution)
                throw std::runtime_error("actual runtime queue returned an absent solution");
            result.push_back(solution->index);
            iterator.postSolution();
        }
        iterator.postProblem();
        return result;
    }

    std::vector<QueueResult> runActualRuntime(std::vector<Row> const& rows,
                                              std::vector<double> const& thresholds)
    {
        using Library = TensileLite::MasterSolutionLibrary<TensileLite::ContractionProblemGemm>;
        auto library = std::make_shared<Library>();
        for(auto const& row : rows)
            library->solutions.emplace(row.ordinal, makeSolution(row));
        auto hardware = makeHardware();
        auto problem = makeProblem(rows.front());
        ActualCheckSolutionAdapter checker(library, hardware);
        for(auto const& row : rows)
        {
            bool actual = checker.checkActual(*library->solutions.at(row.ordinal), problem);
            if(actual != row.checkSolution)
                throw std::runtime_error("actual SolutionIterator::checkSolution differs from fixture");
        }
        auto sorted = actualQueue(1.0, library, hardware, problem);
        std::vector<QueueResult> results;
        for(double threshold : thresholds)
        {
            QueueResult result{};
            result.threshold = threshold;
            result.predictionDisabled = threshold > 1.0;
            result.queuePrefix = actualQueue(threshold, library, hardware, problem);
            result.sortedOrdinals = result.predictionDisabled
                                        ? result.queuePrefix
                                        : sorted;
            if(result.predictionDisabled)
            {
                result.thresholdIndex = -1;
                result.thresholdValue = 0.0;
            }
            else
            {
                result.thresholdIndex = std::min(
                    static_cast<int>(sorted.size()) - 1,
                    static_cast<int>(sorted.size() * threshold));
                int ordinal = sorted.at(result.thresholdIndex);
                result.thresholdValue = rows.at(ordinal).microSeconds;
            }
            results.push_back(std::move(result));
        }
        return results;
    }

    void emitIntegerArray(std::ostream& output, std::vector<int> const& values)
    {
        output << '[';
        for(size_t index = 0; index < values.size(); ++index)
        {
            if(index)
                output << ',';
            output << values[index];
        }
        output << ']';
    }

    void emitDouble(std::ostream& output, double value)
    {
        if(!std::isfinite(value) || (value == 0.0 && std::signbit(value)))
            throw std::runtime_error("non-finite or negative-zero JSON number");
        output << std::setprecision(17) << value;
    }

    void writeTranscript(std::filesystem::path const& path,
                         std::vector<Row> const& rows,
                         std::vector<QueueResult> const& queues)
    {
        if(std::filesystem::exists(path))
            throw std::runtime_error("refusing to overwrite transcript");
        std::ofstream output(path, std::ios::binary | std::ios::out);
        if(!output)
            throw std::runtime_error("cannot create transcript");
        output << "{\"fixture_id\":\"s10r4-native-whole-cohort-v1\",\"queues\":[";
        for(size_t thresholdOrdinal = 0; thresholdOrdinal < queues.size(); ++thresholdOrdinal)
        {
            if(thresholdOrdinal)
                output << ',';
            auto const& queue = queues[thresholdOrdinal];
            double threshold = queue.threshold;
            output << "{\"prediction_disabled\":";
            if(queue.predictionDisabled)
            {
                output << "true,\"queue_prefix\":";
                emitIntegerArray(output, queue.queuePrefix);
                output << ",\"sorted_ordinals\":";
                emitIntegerArray(output, queue.sortedOrdinals);
                output << ",\"threshold\":";
                emitDouble(output, threshold);
                output << ",\"threshold_index\":null,\"threshold_value\":null}";
                continue;
            }
            output << "false,\"queue_prefix\":";
            emitIntegerArray(output, queue.queuePrefix);
            output << ",\"sorted_ordinals\":";
            emitIntegerArray(output, queue.sortedOrdinals);
            output << ",\"threshold\":";
            emitDouble(output, threshold);
            output << ",\"threshold_index\":" << queue.thresholdIndex << ",\"threshold_value\":";
            emitDouble(output, queue.thresholdValue);
            output << '}';
        }
        output << "],\"rows\":[";
        for(size_t index = 0; index < rows.size(); ++index)
        {
            if(index)
                output << ',';
            auto const& row = rows[index];
            output << "{\"checkSolution\":" << (row.checkSolution ? "true" : "false")
                   << ",\"microSeconds\":";
            if(row.checkSolution)
                emitDouble(output, row.microSeconds);
            else
                output << "null";
            output << ",\"ordinal\":" << row.ordinal
                   << ",\"problem_constants\":{\"compute_type\":\"Float\","
                      "\"data_type\":\"BFloat16\",\"transpose_a\":false,"
                      "\"transpose_b\":false}}";
        }
        output << "],\"schema_version\":1,\"tie_ordinals\":[0,2]}\n";
        output.flush();
        if(!output)
            throw std::runtime_error("transcript write failed");
    }
}

int main(int argc, char** argv)
{
    try
    {
        if(argc != 5 || std::string_view(argv[1]) != "--input"
           || std::string_view(argv[3]) != "--output")
            throw std::runtime_error("expected --input PATH --output PATH");
        auto lines = readStrictLines(argv[2]);
        if(lines.size() != 9 || lines[0] != "4 4")
            throw std::runtime_error("fixture header/line count mismatch");
        std::array<std::string, 4> thresholdLines{"0.0 0.0", "0.5 0.5", "1.0 1.0", "2.0 2.0"};
        std::vector<double> thresholds{0.0, 0.5, 1.0, 2.0};
        for(size_t index = 0; index < thresholdLines.size(); ++index)
            if(lines[index + 1] != thresholdLines[index])
                throw std::runtime_error("fixture threshold grammar mismatch");
        std::vector<Row> rows;
        for(size_t index = 0; index < 4; ++index)
        {
            rows.push_back(parseRow(lines[index + 5]));
            if(rows.back().ordinal != static_cast<int>(index))
                throw std::runtime_error("fixture row ordinal mismatch");
            rows.back().microSeconds = predict(rows.back());
        }
        auto queues = runActualRuntime(rows, thresholds);
        writeTranscript(argv[4], rows, queues);
        return 0;
    }
    catch(std::exception const& error)
    {
        std::cerr << error.what() << '\n';
        return 2;
    }
}
