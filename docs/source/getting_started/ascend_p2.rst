P2 paired vLLM integration
==========================

For the P3 branch, see :doc:`ascend_p3`. This page describes the retained P2
delivery, not the P3 package pair.

Use the delivered ``p2`` commit with ``vllm==0.18.0+ascend.p2``. This LMCache
package remains ``0.4.3+ascend.p1`` because its native integration is P3, but an
older same-version LMCache wheel is not interchangeable: the vLLM diagnostic
bridge, live-source event-handoff key and shared Mooncake transport now resolve
through native ``vllm.distributed.kv_transfer`` owners.

The ``p1`` and ``main`` branches retain the P1 input
``547ae7c10b0e510b864c8d0f5233d6f54f279359``. P1 retests and known defect fixes
remain deferred. No cache protocol, layout or recovery algorithm is changed by
this paired import migration. Historical installation patch tools and
``lmcache_ascend`` native integration await P3; do not run the old four-package
patch installer against the P2 vLLM distribution.

The existing ``p1_dev.py`` build, strict editable and verify commands remain
valid with the P2 package pair. Use both exact commits from the workspace
``design/p2/baseline/p2-native-integration-20260927.json`` and rebuild in the
prepared intranet environment. The 22 local installation contract tests pass;
they do not replace extension/ABI, cache, P/D or recovery validation. Detailed
commands and the combined matrix are in ``design/p2/intranet-validation.md``.
