# -*- mode:python -*-

# Copyright (c) 2013 ARM Limited
# All rights reserved.
#
# The license below extends only to copyright in the software and shall
# not be construed as granting a license to any other intellectual
# property including but not limited to intellectual property relating
# to a hardware implementation of the functionality of the software
# licensed hereunder.  You may use the software subject to the license
# terms below provided that you ensure that this notice is replicated
# unmodified and in its entirety in all distributions of the software,
# modified or unmodified, in source code or in binary form.
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

import os

Import('main')

#if not os.path.exists(Dir('.').srcnode().abspath + '/updown'):
#    main['HAVE_UPDOWN'] = False
#    Return()

# We have got the folder, so add the library and build the wrappers
main['HAVE_UPDOWN'] = True


updownlib_path = os.path.join(Dir('#').abspath, 'ext/updown/install/updown/lib')
updowncpp_path = os.path.join(Dir('#').abspath, 'ext/updown/install/updown/lib')
updownh_path = os.path.join(Dir('#').abspath, 'ext/updown/install/updown/include')
updown_path = os.path.join(Dir('#').abspath, 'ext/updown/simruntime')
updownbasim_path = os.path.join(Dir('#').abspath, 'ext/updown/basimruntime')
#updownpyint_path = os.path.join(Dir('#').abspath, 'ext/updown/install/simruntime/')
#updownapp_path = os.path.join(Dir('#').abspath, 'ext/updown/install/simruntime/')

main.Prepend(CPPPATH=Dir('.'))
# a little hacky but can get a shared library working
main.Append(LIBS=['UpDownPyIntf', 'UpDownRuntime', 'UpDownSimRuntime', 'UpDownBASimRuntime', 'UDAccelerator', 'LaneElements', 'ISAElements'],
            LIBPATH=[updownlib_path],  # compile-time lookup
            RPATH=[updownlib_path],  # runtime lookup
            CPPPATH=[updown_path + '/src/'])
