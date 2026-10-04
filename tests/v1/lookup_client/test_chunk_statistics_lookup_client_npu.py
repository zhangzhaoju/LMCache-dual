# SPDX-License-Identifier: Apache-2.0
# Third Party
from tests.v1.lookup_client.test_chunk_statistics_lookup_client import (
    TestBloomFilter as UpstreamBloomFilterTests,
)
from tests.v1.lookup_client.test_chunk_statistics_lookup_client import (
    TestChunkStatisticsBasic as UpstreamChunkStatisticsBasicTests,
)
from tests.v1.lookup_client.test_chunk_statistics_lookup_client import (
    TestChunkStatisticsLifecycle as UpstreamChunkStatisticsLifecycleTests,
)
from tests.v1.lookup_client.test_chunk_statistics_lookup_client import (
    TestChunkStatisticsMetrics as UpstreamChunkStatisticsMetricsTests,
)
from tests.v1.lookup_client.test_chunk_statistics_lookup_client import (
    TestChunkStatisticsPerformance as UpstreamChunkStatsticsPerformanceTests,
)
from tests.v1.lookup_client.test_chunk_statistics_lookup_client import (
    TestFileHashStrategy as UpstreamTestFileHashStrategyTests,
)
from tests.v1.lookup_client.test_chunk_statistics_lookup_client import (
    TestStrategyDiscovery as UpstreamStrategyDiscoveryTests,
)


class TestStrategyDiscovery(UpstreamStrategyDiscoveryTests):
    pass


class TestBloomFilter(UpstreamBloomFilterTests):
    pass


class TestChunkStatisticsBasic(UpstreamChunkStatisticsBasicTests):
    pass


class TestChunkStatisticsMetrics(UpstreamChunkStatisticsMetricsTests):
    pass


class TestChunkStatisticsLifecycle(UpstreamChunkStatisticsLifecycleTests):
    pass


class TestChunkStatisticsPerformance(UpstreamChunkStatsticsPerformanceTests):
    pass


class TestFileHashStrategy(UpstreamTestFileHashStrategyTests):
    pass
