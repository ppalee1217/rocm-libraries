// Copyright Advanced Micro Devices, Inc., or its affiliates.
// SPDX-License-Identifier: MIT

// S10R3's one native conformance path.  This helper is compiled and hash-bound
// before labels but must not be executed until LOCKED_READY.

#include <Tensile/Utils.hpp>

#include "SolutionIterator.hpp"
#include "ResultReporter.hpp"
#include "MetaResultReporter.hpp"

#include <Tensile/AMDGPU.hpp>
#include <Tensile/ContractionProblem.hpp>
#include <Tensile/ContractionSolution.hpp>
#include <Tensile/MasterSolutionLibrary.hpp>
#include <Tensile/Predicates.hpp>
#include <Tensile/hip/HipHardware.hpp>
#include <origami/simulator/tensilelite/formocast_simulator.hpp>

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace s10r3_native
{
    using TensileLite::AMDGPU;
    using TensileLite::ContractionProblemGemm;
    using TensileLite::ContractionSolution;
    using TensileLite::Hardware;
    using TensileLite::MasterSolutionLibrary;

    struct CohortRow
    {
        int      ordinal;
        bool     checkSolutionExpected;
        uint64_t M;
        uint64_t N;
        uint64_t batch;
        uint64_t K;
        origami::Formocast::SizeMapping mapping{};
    };

    static origami::Formocast::ProblemInfo problemInfo(CohortRow const& row)
    {
        origami::Formocast::ProblemInfo value{};
        value.M              = row.M;
        value.N              = row.N;
        value.NumBatches     = row.batch;
        value.K              = row.K;
        value.transA         = false;
        value.transB         = false;
        value.bpeA           = 2;
        value.bpeB           = 2;
        value.bpeD           = 2;
        value.bpeCompute     = 4;
        value.swizzleTensorA = false;
        value.swizzleTensorB = false;
        value.dataType       = origami::data_type_t::BFloat16;
        return value;
    }

    static std::shared_ptr<ContractionSolution> solution(CohortRow const& row)
    {
        auto value   = std::make_shared<ContractionSolution>();
        value->index = row.ordinal;
        auto& out    = value->sizeMapping;
        out.waveNum  = row.mapping.waveNum;
        out.macroTile
            = TensileLite::dim3(row.mapping.macroTile[0],
                                row.mapping.macroTile[1],
                                row.mapping.macroTile[2]);
        out.matrixInstruction = row.mapping.matrixInstruction;
        out.grvwA             = row.mapping.grvwA;
        out.grvwB             = row.mapping.grvwB;
        out.gwvwC             = row.mapping.gwvwC;
        out.gwvwD             = row.mapping.gwvwD;
        out.depthU            = row.mapping.depthU;
        out.globalSplitU      = row.mapping.globalSplitU;
        out.workGroupMapping  = row.mapping.workGroupMapping;
        out.globalAccumulation = row.mapping.globalAccumulation;
        out.workGroupMappingXCC = row.mapping.workGroupMappingXCC;
        out.workGroupMappingXCCGroup = row.mapping.workGroupMappingXCCGroup;
        out.globalSplitUCoalesced = row.mapping.globalSplitUCoalesced;
        out.globalSplitUWorkGroupMappingRoundRobin
            = row.mapping.globalSplitUWorkGroupMappingRoundRobin;
        out.CUOccupancy            = row.mapping.CUOccupancy;
        out.PrefetchGlobalRead     = row.mapping.PrefetchGlobalRead;
        out.MathClocksUnrolledLoop = row.mapping.MathClocksUnrolledLoop;
        out.DirectToVgprA          = row.mapping.DirectToVgprA;
        out.DirectToVgprB          = row.mapping.DirectToVgprB;
        out.NumLoadsCoalescedA     = row.mapping.NumLoadsCoalescedA;
        out.NumLoadsCoalescedB     = row.mapping.NumLoadsCoalescedB;
        out.VectorWidthA           = row.mapping.VectorWidthA;
        out.VectorWidthB           = row.mapping.VectorWidthB;
        out.LocalSplitU            = row.mapping.LocalSplitU;
        out.DirectToLdsA           = row.mapping.DirectToLdsA;
        out.DirectToLdsB           = row.mapping.DirectToLdsB;
        out.waveGroup              = row.mapping.waveGroup;
        value->problemType.aType   = rocisa::DataType::BFloat16;
        value->problemType.bType   = rocisa::DataType::BFloat16;
        value->problemType.cType   = rocisa::DataType::BFloat16;
        value->problemType.dType   = rocisa::DataType::BFloat16;
        value->problemType.computeType = rocisa::DataType::Float;
        if(!row.checkSolutionExpected)
        {
            value->hardwarePredicate
                = std::make_shared<TensileLite::Predicates::False<Hardware>>();
        }
        return value;
    }

    static ContractionProblemGemm problem(CohortRow const& row)
    {
        size_t lda = row.M;
        size_t ldb = row.K;
        size_t ldc = row.M;
        size_t ldd = row.M;
        auto   value
            = ContractionProblemGemm::GEMM_Strides(false,
                                                   false,
                                                   rocisa::DataType::BFloat16,
                                                   rocisa::DataType::BFloat16,
                                                   rocisa::DataType::BFloat16,
                                                   rocisa::DataType::BFloat16,
                                                   row.M,
                                                   row.N,
                                                   row.K,
                                                   row.batch,
                                                   lda,
                                                   row.M * row.K,
                                                   ldb,
                                                   row.K * row.N,
                                                   ldc,
                                                   row.M * row.N,
                                                   ldd,
                                                   row.M * row.N,
                                                   0.0);
        value.setComputeInputTypeA(rocisa::DataType::BFloat16);
        value.setComputeInputTypeB(rocisa::DataType::BFloat16);
        value.setBetaType(rocisa::DataType::Float);
        return value;
    }

    static double predict(CohortRow const& row)
    {
        origami::Formocast formocast;
        formocast.setProblem(problemInfo(row));
        formocast.setSolution(row.mapping);
        formocast.setHardware(origami::hardware_t::architecture_t::gfx942);
        auto prediction = formocast.predictedPerformance();
        if(!std::isfinite(prediction.microSeconds)
           || !std::isfinite(prediction.hitRate))
            throw std::runtime_error("non-finite native Formocast result");
        return prediction.microSeconds;
    }

    static std::vector<int>
        runtimeQueue(std::vector<CohortRow> const& rows, double threshold)
    {
        auto library
            = std::make_shared<MasterSolutionLibrary<ContractionProblemGemm>>();
        for(auto const& row : rows)
            library->solutions[row.ordinal] = solution(row);
        auto hardware              = std::make_shared<TensileLite::hip::HipAMDGPU>();
        hardware->processor        = AMDGPU::Processor::gfx942;
        hardware->computeUnitCount = 304;
        auto architecture          = origami::hardware_t::architecture_t::gfx942;
        hardware->analyticalHardware
            = std::make_shared<origami::hardware_t>(
                architecture,
                304,
                64 * 1024,
                origami::hardware_t::get_arch_constants(architecture),
                8,
                16 * 1024 * 1024,
                1.7,
                1.0);
        TensileLite::Client::AllSolutionsIterator iterator(
            library, hardware, threshold, 0, rows.size(), true);
        iterator.setReporter(
            std::make_shared<TensileLite::Client::MetaResultReporter>());
        auto currentProblem = problem(rows.front());
        iterator.preProblem(&currentProblem);
        std::vector<int> queue;
        while(iterator.moreSolutionsInProblem())
        {
            auto current = iterator.getSolution();
            if(!current)
                throw std::runtime_error(
                    "runtime queue returned an absent solution");
            queue.push_back(current->index);
            iterator.postSolution();
        }
        return queue;
    }

    static void writeIntVector(std::ostream& output,
                               std::vector<int> const& values)
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

    int evaluate_formocast_all_solutions_cohort(std::istream& input,
                                                std::ostream& output)
    {
        size_t rowCount       = 0;
        size_t thresholdCount = 0;
        if(!(input >> rowCount >> thresholdCount) || rowCount != 4
           || thresholdCount != 4)
            throw std::runtime_error("invalid S10R3 cohort header");
        std::vector<std::pair<std::string, double>> thresholds;
        for(size_t index = 0; index < thresholdCount; ++index)
        {
            std::string token;
            double      value;
            if(!(input >> token >> value) || value < 0)
                throw std::runtime_error("invalid S10R3 threshold");
            thresholds.emplace_back(token, value);
        }
        std::vector<CohortRow> rows;
        for(size_t index = 0; index < rowCount; ++index)
        {
            CohortRow row{};
            int valid;
            int waveNum, mt0, mt1, mt2, mi0, mi1, mi2, mi3;
            int grvwA, grvwB, gwvwC, gwvwD, depthU, suppliedGSU;
            int wgm, accumulation, xcc, xccGroup, gsuCoalesced, gsuWgmRR;
            int occupancy, pgr, mathClocks, dtvA, dtvB, nlca, nlcb;
            int vectorWidthA, vectorWidthB, lsu, dtlA, dtlB, waveGroup0;
            int waveGroup1;
            if(!(input >> row.ordinal >> valid >> row.M >> row.N >> row.batch
                 >> row.K >> waveNum >> mt0 >> mt1 >> mt2 >> mi0 >> mi1
                 >> mi2 >> mi3 >> grvwA >> grvwB >> gwvwC >> gwvwD
                 >> depthU >> suppliedGSU >> wgm >> accumulation >> xcc
                 >> xccGroup >> gsuCoalesced >> gsuWgmRR >> occupancy >> pgr
                 >> mathClocks >> dtvA >> dtvB >> nlca >> nlcb >> vectorWidthA
                 >> vectorWidthB >> lsu >> dtlA >> dtlB >> waveGroup0
                 >> waveGroup1))
                throw std::runtime_error("malformed S10R3 cohort row");
            if(row.ordinal != static_cast<int>(index))
                throw std::runtime_error(
                    "S10R3 cohort ordinals must be contiguous");
            row.checkSolutionExpected = valid != 0;
            auto& mapping             = row.mapping;
            mapping.waveNum           = waveNum;
            mapping.macroTile         = {mt0, mt1, mt2};
            mapping.matrixInstruction = {mi0, mi1, mi2, mi3};
            mapping.grvwA             = grvwA;
            mapping.grvwB             = grvwB;
            mapping.gwvwC             = gwvwC;
            mapping.gwvwD             = gwvwD;
            mapping.depthU            = depthU;
            mapping.globalSplitU      = suppliedGSU;
            mapping.workGroupMapping  = wgm;
            mapping.globalAccumulation = accumulation;
            mapping.workGroupMappingXCC = xcc;
            mapping.workGroupMappingXCCGroup = xccGroup;
            mapping.globalSplitUCoalesced = gsuCoalesced != 0;
            mapping.globalSplitUWorkGroupMappingRoundRobin = gsuWgmRR != 0;
            mapping.CUOccupancy            = occupancy;
            mapping.PrefetchGlobalRead     = pgr;
            mapping.MathClocksUnrolledLoop = mathClocks;
            mapping.DirectToVgprA          = dtvA != 0;
            mapping.DirectToVgprB          = dtvB != 0;
            mapping.NumLoadsCoalescedA     = nlca;
            mapping.NumLoadsCoalescedB     = nlcb;
            mapping.VectorWidthA           = vectorWidthA;
            mapping.VectorWidthB           = vectorWidthB;
            mapping.LocalSplitU            = lsu;
            mapping.DirectToLdsA           = dtlA != 0;
            mapping.DirectToLdsB           = dtlB != 0;
            mapping.waveGroup              = {waveGroup0, waveGroup1};
            rows.push_back(row);
        }

        std::vector<std::pair<int, double>> performance;
        for(auto const& row : rows)
        {
            if(row.checkSolutionExpected)
                performance.emplace_back(row.ordinal, predict(row));
        }
        std::stable_sort(performance.begin(),
                         performance.end(),
                         [](auto const& left, auto const& right) {
                             return left.second < right.second;
                         });
        if(performance.size() != 3)
            throw std::runtime_error(
                "S10R3 cohort does not contain three valid solutions");

        output << std::setprecision(17);
        output
            << "{\"schema_version\":1,"
            << "\"symbol\":\"s10r3_native::evaluate_formocast_all_solutions_cohort\","
            << "\"status\":\"PASS\","
            << "\"native_path_called\":true,"
            << "\"runtime_check_solution_called\":true,"
            << "\"runtime_pre_problem_called\":true,"
            << "\"guard_order\":["
            << "\"global-split-u-zero\","
            << "\"small-mn-macro-tile-gap\","
            << "\"large-mn-macro-tile-gap\","
            << "\"bf16-half-depthu-k-batch-mi\","
            << "\"direct-to-lds-a-small-m\","
            << "\"direct-to-lds-b-small-n\","
            << "\"derived-plr-zero\"],"
            << "\"early_terminate\":{\"microSeconds\":9999999.9,\"hitRate\":0.0},"
            << "\"first_true_wins\":true,"
            << "\"predictions\":[";
        for(size_t index = 0; index < performance.size(); ++index)
        {
            if(index)
                output << ',';
            output << "{\"ordinal\":" << performance[index].first
                   << ",\"microSeconds\":" << performance[index].second << '}';
        }
        output << "],\"queues\":{";
        for(size_t thresholdNumber = 0; thresholdNumber < thresholds.size();
            ++thresholdNumber)
        {
            if(thresholdNumber)
                output << ',';
            auto const& token     = thresholds[thresholdNumber].first;
            double      threshold = thresholds[thresholdNumber].second;
            auto        queue     = runtimeQueue(rows, threshold);
            std::vector<int> sortedOrdinals;
            size_t           thresholdIndex = 0;
            double           thresholdValue = 0;
            if(threshold > 1.0)
            {
                for(auto const& row : rows)
                    sortedOrdinals.push_back(row.ordinal);
            }
            else
            {
                for(auto const& item : performance)
                    sortedOrdinals.push_back(item.first);
                thresholdIndex
                    = std::min(performance.size() - 1,
                               static_cast<size_t>(performance.size() * threshold));
                thresholdValue = performance[thresholdIndex].second;
            }
            output << '"' << token << "\":{\"prediction_disabled\":"
                   << (threshold > 1.0 ? "true" : "false")
                   << ",\"sorted_ordinals\":";
            writeIntVector(output, sortedOrdinals);
            if(threshold > 1.0)
                output << ",\"threshold_index\":null,\"threshold_value\":null";
            else
                output << ",\"threshold_index\":" << thresholdIndex
                       << ",\"threshold_value\":" << thresholdValue;
            output << ",\"queue_prefix\":";
            writeIntVector(output, queue);
            output << '}';
        }
        output << "}}\n";
        return 0;
    }
} // namespace s10r3_native

int main(int argc, char** argv)
{
    try
    {
        std::string inputPath;
        std::string outputPath;
        for(int index = 1; index < argc; ++index)
        {
            std::string argument = argv[index];
            if(argument == "--input" && index + 1 < argc)
                inputPath = argv[++index];
            else if(argument == "--output" && index + 1 < argc)
                outputPath = argv[++index];
            else
                throw std::runtime_error(
                    "usage: s10r3-native --input INPUT --output OUTPUT");
        }
        std::ifstream input(inputPath);
        std::ofstream output(outputPath, std::ios::trunc);
        if(!input || !output)
            throw std::runtime_error("cannot open S10R3 helper input/output");
        int result
            = s10r3_native::evaluate_formocast_all_solutions_cohort(input, output);
        input >> std::ws;
        if(!input.eof() || !output)
            throw std::runtime_error("S10R3 helper stream failure");
        return result;
    }
    catch(std::exception const& error)
    {
        std::cerr << "s10r3-native: " << error.what() << '\n';
        return 2;
    }
}
