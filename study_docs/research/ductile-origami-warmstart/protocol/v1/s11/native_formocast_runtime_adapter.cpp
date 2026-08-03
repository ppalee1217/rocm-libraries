// Copyright Advanced Micro Devices, Inc., or its affiliates.
// SPDX-License-Identifier: MIT

// S11's only native scoring implementation.  Input is a deliberately small,
// positional protocol produced by native_adapter.py after Python has verified
// the effective lock and helper hash.  This source constructs the pinned
// Formocast ProblemInfo and SizeMapping objects and calls predictedPerformance
// for every (exactly three) locked size.  It does not provide a proxy formula.

#include <origami/simulator/tensilelite/formocast_simulator.hpp>

#include <cmath>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace s11_native
{
    struct Request
    {
        std::string requestSha256;
        std::string semanticIdentity;
        std::vector<std::vector<unsigned long long>> sizes;
        origami::Formocast::SizeMapping mapping{};
    };

    static Request readRequest(std::istream& input)
    {
        std::string protocol;
        size_t      sizeCount = 0;
        Request     request;
        if(!(input >> protocol >> request.requestSha256 >> request.semanticIdentity >> sizeCount)
           || protocol != "S11_NATIVE_FORMOCAST_V1" || sizeCount != 3)
            throw std::runtime_error("invalid S11 native protocol/header");
        request.sizes.resize(sizeCount, std::vector<unsigned long long>(4));
        for(auto& size : request.sizes)
            if(!(input >> size[0] >> size[1] >> size[2] >> size[3]))
                throw std::runtime_error("partial S11 locked-size vector");

        int waveNum, mt0, mt1, mt2, mi0, mi1, mi2, mi3;
        int grvwA, grvwB, gwvwC, gwvwD, depthU, globalSplitU;
        int workGroupMapping, globalAccumulation, xcc, xccGroup;
        int gsuCoalesced, gsuRoundRobin, occupancy, prefetch, mathClocks;
        int directA, directB, loadsA, loadsB, vectorA, vectorB;
        int localSplitU, directLdsA, directLdsB, waveGroup0, waveGroup1;
        if(!(input >> waveNum >> mt0 >> mt1 >> mt2 >> mi0 >> mi1 >> mi2 >> mi3
             >> grvwA >> grvwB >> gwvwC >> gwvwD >> depthU >> globalSplitU
             >> workGroupMapping >> globalAccumulation >> xcc >> xccGroup
             >> gsuCoalesced >> gsuRoundRobin >> occupancy >> prefetch >> mathClocks
             >> directA >> directB >> loadsA >> loadsB >> vectorA >> vectorB
             >> localSplitU >> directLdsA >> directLdsB >> waveGroup0 >> waveGroup1))
            throw std::runtime_error("partial S11 SizeMapping projection");
        auto& mapping = request.mapping;
        mapping.waveNum = waveNum;
        mapping.macroTile = {mt0, mt1, mt2};
        mapping.matrixInstruction = {mi0, mi1, mi2, mi3};
        mapping.grvwA = grvwA;
        mapping.grvwB = grvwB;
        mapping.gwvwC = gwvwC;
        mapping.gwvwD = gwvwD;
        mapping.depthU = depthU;
        mapping.globalSplitU = globalSplitU;
        mapping.workGroupMapping = workGroupMapping;
        mapping.globalAccumulation = globalAccumulation;
        mapping.workGroupMappingXCC = xcc;
        mapping.workGroupMappingXCCGroup = xccGroup;
        mapping.globalSplitUCoalesced = gsuCoalesced != 0;
        mapping.globalSplitUWorkGroupMappingRoundRobin = gsuRoundRobin != 0;
        mapping.CUOccupancy = occupancy;
        mapping.PrefetchGlobalRead = prefetch;
        mapping.MathClocksUnrolledLoop = mathClocks;
        mapping.DirectToVgprA = directA != 0;
        mapping.DirectToVgprB = directB != 0;
        mapping.NumLoadsCoalescedA = loadsA;
        mapping.NumLoadsCoalescedB = loadsB;
        mapping.VectorWidthA = vectorA;
        mapping.VectorWidthB = vectorB;
        mapping.LocalSplitU = localSplitU;
        mapping.DirectToLdsA = directLdsA != 0;
        mapping.DirectToLdsB = directLdsB != 0;
        mapping.waveGroup = {waveGroup0, waveGroup1};
        if(mapping.globalSplitU < 1)
            throw std::runtime_error("unresolved/auto GlobalSplitU is forbidden");
        std::string trailing;
        if(input >> trailing)
            throw std::runtime_error("unknown trailing S11 native input");
        return request;
    }

    static origami::Formocast::ProblemInfo problemInfo(
        std::vector<unsigned long long> const& size)
    {
        origami::Formocast::ProblemInfo problem{};
        problem.M = size[0];
        problem.N = size[1];
        problem.NumBatches = size[2];
        problem.K = size[3];
        problem.transA = false;
        problem.transB = false;
        problem.bpeA = 2;
        problem.bpeB = 2;
        problem.bpeD = 2;
        problem.bpeCompute = 4;
        problem.swizzleTensorA = false;
        problem.swizzleTensorB = false;
        problem.dataType = origami::data_type_t::BFloat16;
        return problem;
    }

    static double predict(Request const& request, std::vector<unsigned long long> const& size)
    {
        origami::Formocast model;
        model.setProblem(problemInfo(size));
        model.setSolution(request.mapping);
        model.setHardware(origami::hardware_t::architecture_t::gfx942);
        auto prediction = model.predictedPerformance();
        if(!std::isfinite(prediction.microSeconds) || prediction.microSeconds <= 0.0)
            throw std::runtime_error("non-finite/non-positive native Formocast result");
        return prediction.microSeconds;
    }

    static void writeResponse(Request const& request, std::ostream& output)
    {
        output << std::setprecision(17)
               << "{\"latencies\":[";
        for(size_t index = 0; index < request.sizes.size(); ++index)
        {
            if(index)
                output << ',';
            auto const& size = request.sizes[index];
            output << "{\"predicted_latency\":" << predict(request, size)
                   << ",\"problem_size\":[" << size[0] << ',' << size[1] << ','
                   << size[2] << ',' << size[3] << "]}";
        }
        output << "],\"native_path_called\":true,\"protocol\":\"s11_native_formocast_v1\""
               << ",\"request_sha256\":\"" << request.requestSha256 << "\""
               << ",\"semantic_identity\":\"" << request.semanticIdentity << "\"}\n";
    }
}

int main()
{
    try
    {
        auto request = s11_native::readRequest(std::cin);
        s11_native::writeResponse(request, std::cout);
        return 0;
    }
    catch(std::exception const& error)
    {
        std::cerr << "S11 native helper failed closed: " << error.what() << '\n';
        return 23;
    }
}
