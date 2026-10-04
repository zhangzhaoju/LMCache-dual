# SPDX-License-Identifier: Apache-2.0

# The Python builder reads CANN's case-sensitive Ascend910B3.ini and passes
# that spelling here. Compare case-insensitively, without widening the profile.
string(TOLOWER "${SOC_VERSION}" _lmcache_soc_lower)
if(NOT _lmcache_soc_lower STREQUAL "ascend910b3")
    message(FATAL_ERROR
        "P4 supports only SOC_VERSION=ascend910b3 (got '${SOC_VERSION}')")
endif()
unset(_lmcache_soc_lower)

# Preserve the CANN spelling for kvcache-ops and its nested builds.
set(SOC_VERSION "Ascend910B3")
