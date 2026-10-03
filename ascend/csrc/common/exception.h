#pragma once
#include "torch/extension.h"
#define LMCACHE_ASCEND_CHECK(...) TORCH_CHECK(__VA_ARGS__)
