# SPDX-License-Identifier: Apache-2.0
cmake_minimum_required(VERSION 3.26.1)
project(lmcache_ascend_unified LANGUAGES C CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(PYBIND11_FINDPYTHON ON)
find_package(Python3 COMPONENTS Interpreter Development.Module REQUIRED)
find_package(pybind11 REQUIRED)
find_package(Threads REQUIRED)
find_package(Torch REQUIRED)
if(NOT DEFINED GLIBCXX_USE_CXX11_ABI OR NOT DEFINED P1_HOST_INSTALL_DIR)
  message(FATAL_ERROR "Use the unified Python build entry to supply ABI/install paths")
endif()
add_compile_definitions(_GLIBCXX_USE_CXX11_ABI=${GLIBCXX_USE_CXX11_ABI})
add_subdirectory(ascend)

# Host allocators/storage must not be lost with NO_CUDA_EXT.
pybind11_add_module(native_storage_ops
  csrc/storage_manager/bitmap.cpp csrc/storage_manager/pybind.cpp
  csrc/storage_manager/ttl_lock.cpp csrc/storage_manager/utils.cpp)
foreach(backend fs redis)
  pybind11_add_module(lmcache_${backend}
    csrc/storage_backends/${backend}/pybind.cpp
    csrc/storage_backends/${backend}/connector.cpp)
  target_include_directories(lmcache_${backend} PRIVATE csrc/storage_backends
    csrc/storage_backends/${backend})
  target_link_libraries(lmcache_${backend} PRIVATE Threads::Threads)
  install(TARGETS lmcache_${backend} DESTINATION ${P1_HOST_INSTALL_DIR})
endforeach()
target_link_libraries(native_storage_ops PRIVATE Threads::Threads)
install(TARGETS native_storage_ops DESTINATION ${P1_HOST_INSTALL_DIR})

# Optional native L2 client; RemoteFill uses CANN's Python Mooncake.
option(BUILD_MOONCAKE "Build the optional native Mooncake L2 adapter" OFF)
if(BUILD_MOONCAKE)
  if(NOT MOONCAKE_INCLUDE_DIR OR NOT MOONCAKE_LIB_DIR)
    message(FATAL_ERROR "Native Mooncake needs explicit approved headers/libraries")
  endif()
  find_library(MOONCAKE_STORE_LIBRARY NAMES store
    PATHS ${MOONCAKE_LIB_DIR} NO_DEFAULT_PATH REQUIRED)
  pybind11_add_module(lmcache_mooncake csrc/storage_backends/mooncake/pybind.cpp
    csrc/storage_backends/mooncake/connector.cpp)
  target_include_directories(lmcache_mooncake PRIVATE csrc/storage_backends
    csrc/storage_backends/mooncake ${MOONCAKE_INCLUDE_DIR})
  target_compile_features(lmcache_mooncake PRIVATE cxx_std_20)
  target_compile_definitions(lmcache_mooncake PRIVATE YLT_ENABLE_IBV)
  target_link_libraries(lmcache_mooncake PRIVATE ${MOONCAKE_STORE_LIBRARY} Threads::Threads)
  set_target_properties(lmcache_mooncake PROPERTIES INSTALL_RPATH "${MOONCAKE_LIB_DIR}")
  install(TARGETS lmcache_mooncake DESTINATION ${P1_HOST_INSTALL_DIR})
endif()
