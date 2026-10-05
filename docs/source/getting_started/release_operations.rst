Joint P5 P6 qualification and paired cutover
============================================

The final ``p6`` branch inherits all ``p5`` work from the immutable
``native-layout-frozen-20261005`` pair. Qualify this final pair once in the
intranet; do not repeat the full 2P2D campaign on P5. The release changes no
cache, inference or native implementation. ``release-profile.json`` describes
the candidate, not a completed qualification.

Installation and evidence
-------------------------

Follow :doc:`baseline_validation` to reinstall both packages in all four test
containers using the same strict editable and launch commands as native-layout.
This baseline comparison does not require switching to wheels or a new image;
do not change deployment mode or inference parameters just for this comparison.
Install both candidate distributions in every test container with standard pip.
Root ``setup.py`` implements editable, ``bdist_wheel`` and ``sdist``; the read-only
``tools/check_native_layout.py`` checks installed paths or wheel contents.
Do not switch a running editable checkout or update only one
package. Formal release qualification still covers ordinary wheels, sdist
rebuilds and a clean image with a digest-pinned prepared base. Label editable
evidence accurately; it is not wheel/image evidence. The reviewer decides which
functional evidence can be reused based on provenance and installation differences.

Keep Python 3.11/aarch64, CANN 8.5.1, torch 2.9.0, torch-npu 2.9.0.post2,
transformers 5.2.0 and triton-ascend 3.2.0.dev20260322 unchanged. Build/install
does not resolve dependencies or download models. Prepare fixed materials via
approved intranet sources/proxy; never connect the intranet to external AI agents.

Record source SHAs, wheel hashes, image digests, materials, installation paths
and per-container checks. Cover offline/online GLM-5.2, DSA dual groups, MTP,
C8-off, TP8/DP2 and TP4/DP4, CPU KV, P/D, RemoteFill and recovery. Compare cold
and warm performance separately with at least three complete repeats and real
wall time. Errors, zero-output and interrupted runs do not qualify. Native-layout
logs showed the primary path working, but tail-latency equivalence remains pending.

Cutover and rollback
---------------------

Production cutover waits for reviewed functionality, performance, soak, artifact
and recovery evidence. First restore the frozen pair in an independent environment
and verify model/config/material access. Stop new traffic, drain or cancel in-flight
requests, finish asynchronous stores/transfers, then deploy both matched packages,
configuration and image together. Follow the existing RemoteFill paired-restart
protocol. Keep old and new persistent cache namespaces separate unless compatibility
has been explicitly demonstrated.

Rollback includes both distributions, native libraries, configuration, image and
the old namespace. A source bundle does not contain models, LFS object payloads,
uncommitted/ignored files, external configuration or the installed environment.
Do not retire the original four checkouts before these materials and a recovery
exercise are complete. Host tools never switch live services or delete repositories;
missing intranet results remain pending.
