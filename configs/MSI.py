# Copyright (c) 2006-2007 The Regents of The University of Michigan
# Copyright (c) 2009 Advanced Micro Devices, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Authors: Brad Beckmann

import math
import m5
from m5.objects import *
from m5.defines import buildEnv
from Ruby import create_topology
from Ruby import send_evicts
#
# Declare caches used by the protocol
#
class L1Cache(RubyCache): pass
class L2Cache(RubyCache): pass

def define_options(parser):
    return

def create_system(options, full_system, system, dma_ports, bootmem,
                  ruby_system):


    if buildEnv['PROTOCOL'] != 'MSI':
        fatal("This script requires the MSI_Two_Level_aladdin protocol to be \
            built.")
    print("made it here")
    # Run the original protocol script
    #buildEnv['PROTOCOL'] = buildEnv['PROTOCOL'][:-8]
    
    protocol = "MESI_Two_Level"
    exec "import %s" % protocol
    
    try:
        (cpu_sequencers, dir_cntrls, topology) = \
            eval("%s.create_system(options, full_system, system, dma_ports, \
                bootmem, ruby_system)" % protocol)
    except:
        print "Error: could not create system for ruby protocol inside fusion \
            system %s" % protocol
        raise

    #
    # Must create the individual controllers before the network to ensure the
    # controller constructors are called before the network constructor
    #
    l2_bits = int(math.log(options.num_l2caches, 2))
    block_size_bits = int(math.log(options.cacheline_size, 2))

    #
    # Build accelerator
    #
    # Accelerator cache
    datapaths = system.find_all(HybridDatapath)[0]
    for i,datapath in enumerate(datapaths):
        l1d_cache = L1Cache(size = options.l1d_size,
                            assoc = options.l1d_assoc,
                            start_index_bit = block_size_bits )
        l1_cntrl = L1Cache_Controller(version = options.num_cpus+i,
                                     # cacheMemory = l1i_cache,
                                      cacheMemory=l1d_cache,
                                      send_evictions = send_evicts(options),
                                      ruby_system = ruby_system,
                                      transitions_per_cycle = options.ports, 
				      number_of_TBEs=1024)

        acc_seq = RubySequencer(version = options.num_cpus+i,
                                icache = l1_cntrl.cacheMemory,
                                dcache = l1_cntrl.cacheMemory,
                                ruby_system = ruby_system)

        l1_cntrl.sequencer = acc_seq
        setattr(ruby_system, "l1_cntrl_acc%d" % i, l1_cntrl)

        # Add controllers and sequencers to the appropriate lists
        cpu_sequencers.append(acc_seq)
        topology.addController(l1_cntrl)

        # Connect the L1 controllers and the network
        l1_cntrl.mandatoryQueue = MessageBuffer()

        l1_cntrl.requestToDir = MessageBuffer()
        l1_cntrl.requestToDir.master = ruby_system.network.slave
        l1_cntrl.responseToDirOrSibling = MessageBuffer()
        l1_cntrl.responseToDirOrSibling.master = ruby_system.network.slave
        
        l1_cntrl.forwardFromDir = MessageBuffer()
        l1_cntrl.forwardFromDir.slave = ruby_system.network.master
        l1_cntrl.responseFromDirOrSibling = MessageBuffer()
        l1_cntrl.responseFromDirOrSibling.slave = ruby_system.network.master

        
        ## ACP port
#        acp_dummy_ic = L1Cache(size = '256B',
#                               assoc = 2,
#                               start_index_bit = block_size_bits,
#                               is_icache = True)
    #    acp_dummy_dc = L1Cache(size = '256B',
    #                           assoc = 2,
    #                           start_index_bit = block_size_bits,
    #                           is_icache = False)
    #    acp_cntrl = ACP_Controller(version = i,
    #                               l2_select_num_bits = l2_bits,
    #                               write_through = True,
    #                               ruby_system = ruby_system)

    #    acp_seq = RubySequencer(version = i,
    #                            icache = acp_dummy_ic,
    #                            dcache = acp_dummy_dc,
    #                            #clk_domain = clk_domain,
    #                            #transitions_per_cycle = options.ports,
    #                            ruby_system = ruby_system)

    #    acp_cntrl.sequencer = acp_seq
    #    setattr(ruby_system, "acp_cntrl_acc%d" % i, acp_cntrl)

    #    # Add controllers and sequencers to the appropriate lists
    #    cpu_sequencers.append(acp_seq)
    #    topology.addController(acp_cntrl)

    #    # Connect the ACP controller and the network
    #    acp_cntrl.mandatoryQueue = MessageBuffer()
    #    acp_cntrl.requestToDir = MessageBuffer()
    #    acp_cntrl.requestToDir.master = ruby_system.network.slave
    #    acp_cntrl.responseFromCache = MessageBuffer(ordered = True)
    #    acp_cntrl.responseFromCache.slave = ruby_system.network.master
#	print("cpu",len(cpu_sequencers))
    return (cpu_sequencers, dir_cntrls, topology)
