# SRAM diagnostic CI — not a release

This branch is authorized only for diagnostic CI. It does not merge into `main`,
submit a Tiny Tapeout revision, generate a replacement layout, or publish Pages.
The historical first submission remains unqualified for fabrication.

## Hypotheses and probes

1. If the Magic crash is specific to the local ARM64 environment, the same
   LibreLane 3.0.5 image release, PDK and input files should not crash on Linux
   x86-64. This comparison changes the platform/tool build, not just the CPU.
2. If this Magic/tool-deck combination is generally affected, the isolated
   provider SRAM should also fail on x86-64.
3. If only the full AstraPIO layout fails while isolated SRAM succeeds, examine
   hierarchy/import integration and the generated SRAM cell-name prefix.

The witnesses are the original provider 256x8 SRAM, the newer provider SRAM,
and the **unchanged submitted AstraPIO GDS**. Input SHA-256 checks are fatal.
The newer macro is never substituted into the submitted GDS.

## Frozen inputs

- Submitted artifact: `10540429315`, run `35328977063`, commit `487ee6c`.
- Corrected Ciel PDK release: `5e6d592e4002946a4616f798c357f0f3c06cf3b6`.
- Old standalone SRAM source: IHP PDK `c4b8b4e5e7a05f375cca3815d51b3a37721fbf5c`.
- Ciel installer: 2.4.0. Ciel installs the PDK; it is not a DRC checker.
- LibreLane image: 3.0.5, pinned multi-platform digest in the workflow,
  executed as `linux/amd64`. Actual Magic/KLayout versions are logged.
- Unmodified `tt-support-tools`: `01d5d2814fa9dd61e9d211e0b235a4a592a9316a`.

## Checks and interpretation

Magic imports all layout geometry using the upstream `read_sram_gds.tcl`, then
runs the minimal DRC reproducer with hierarchy expansion and explicit completion
(`drc catchup`) before reading results. Logs, category counts,
and unfiltered raw violation coordinates are retained if Magic produces them.
A crash, timeout, absent/malformed report or positive count is a failure.
The updated harness was replayed on ARM64 with the old standalone SRAM before
the CI push: exit 139 again, no counts report (`work/diagnostic-arm-replay/`).

The same submitted GDS also runs the ten unmodified Tiny Tapeout IHP prechecks
against the corrected Ciel PDK. The KLayout binary comes from the pinned image;
Python checker dependencies come from the pinned upstream requirements file.
This is **not** the current central shuttle environment: its PDK is still older.
A diagnostic pass cannot confer central-shuttle acceptance or fabrication signoff.

Independent probes all run before the aggregate exit status is returned. Any
failure keeps the workflow red. No `continue-on-error`, SRAM exclusions, category
filters, `--skip` check options or report rewrites are used. Evidence is uploaded
even when the diagnostic fails. Setup failure also fails the workflow.

The branch restores blocking release checks and adds regression tests to reject
the previous provisional bypass. These changes are **not merged into main**.
The ordinary RTL test workflow runs on this branch as well; docs publishing is
excluded on the diagnostic branch and the GDS release workflow is not invoked.

## Local parser/guard verification

```sh
python3 -m unittest discover -s test -p test_sram_diagnostic.py
python3 -m unittest discover -s test -p test_release_policy.py
```

Parser tests exercise synthetic process/report outcomes; they do not claim any
physical DRC success. The CI probes operate on real, hash-verified layout files.

## Follow-up: instrumented Magic version comparison (18 September 2026)

The first x86-64 diagnostic run `35343378810` timed out after 180 seconds for
each of the three Magic probes. The unchanged Tiny Tapeout precheck passed all
10 tests with the corrected Ciel PDK. Those results are independent: the Magic
timeouts remain failures, not zero-error results.

Local ARM64 stage instrumentation then established:

- A nonempty 2 um Metal1 square completes with zero errors.
- The original standalone SRAM imports successfully, selects `drc(full)`, and
  crashes (exit 139) during `drc catchup`.
- Thus PDK startup alone is not the reproducer. The last generic log line did
  not identify the failing operation accurately enough.
- The deliberately invalid 0.1 um Metal1 witness also returns zero with the
  local ARM64 8.3.623 build, even after explicitly covering its full bounding
  box. This is an unresolved checker/harness defect, not a valid physical pass.
  The CI treats failure to detect the negative witness as a blocking failure.

`magic-version-diagnostic.yaml` now runs on this diagnostic branch. The original
container comparison remains available manually; its checks have not been
relaxed. The new comparison builds unmodified upstream Magic sources on Ubuntu
24.04 with the same dependencies and `CFLAGS='-O2 -g'`:

- 8.3.623: `fd12c39c37f26a0fe6e04698b1011e31b8bd3229`.
- 8.3.684: `4f53bb3091d1e4a9b2009a58f157a8a4331d4c84`.

The controlled comparison changes Magic's source version, not the PDK or GDS.
The native 8.3.623 build is also compared with the previous Nix/container build;
differences between those builds cannot be attributed to source version alone.

Each version checks five independent cases: a valid Metal1 square, a deliberately
invalid narrow Metal1 witness, both provider SRAM versions separately, and the
unchanged submitted AstraPIO GDS. The negative witness must produce actual DRC
violations. Both SRAMs and AstraPIO must have zero errors to pass. A timeout,
crash, missing report, or missing completion marker fails. There are no SRAM
exclusions, rule edits, or replacement macro geometry. Stage times, CPU time,
maximum resident memory, raw violation coordinates, and hashes are archived.

Motivating upstream changes (hypotheses, not yet proven causes):

- [DRC exception signed-char fix](https://github.com/RTimothyEdwards/magic/commit/e789f18523a1faa63060cf992d04a7b982653b19).
- [Removal of reentrant event processing during DRC](https://github.com/RTimothyEdwards/magic/commit/06eab7feb6d8c6533d7d75d939fb1d4f25e809cc).

A successful diagnostic would still require qualification in the official shuttle
environment. It is not permission to omit any fabrication check.
