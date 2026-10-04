# Frozen notebook fragments — constructed DEMO

All numbers and mechanisms below are designed for a writing/illustration trial. No physical or computational experiment was run. The manuscript must not imply otherwise. There is no supplied prior-art search. The finite-volume stencil, rectangular partitioning, and asynchronous work queue are inherited from an earlier teaching implementation; authors did not invent them here.

## Code notes, not manuscript prose

The program advances a scalar diffusion field on a 2D rectangular grid with four equal rectangular patches. Their topological placement is W0 upper left, W1 upper right, W2 lower left, W3 lower right. Grid size depends on case. Only edge-neighbour patches exchange ghost values; diagonally touching patches do not exchange in this model. Interior cells and one edge ghost layer belong to each patch. A ghost value is a copied neighbour value used in a stencil, not an extra physical cell. The outline is topological; no metres, material thickness, or 3D domain was supplied.

At step k, boundary update of a patch requires all applicable neighbour edge values labelled (partition_epoch,k). Interior work may run while messages travel. When a partition epoch changes, queued messages from earlier epochs must not be consumed. Source notes do not give a physical packet route, link speed or processor shape.

B uses the existing work queue but waits at a global barrier at every step; one incoming buffer per interface is enough because no producer advances through the barrier early. U removes that global barrier and overwrites its one incoming buffer whenever a new message arrives. It performs a boundary update with the latest values currently present, without testing their step labels. G also removes the global barrier. It allocates two incoming slots per interface; each holds values, epoch, step and a ready flag. A reader selects only a ready slot whose epoch/step equal its required pair. A producer cannot overwrite a slot until the consumer acknowledges release. If both slots remain live, that interface's producer waits. Two slots do not promise unbounded overlap. There is no faster numerical stencil in G, and no new mesh partitioning method.

An illustrative legal interleaving in the debugging notebook (not a frequency measurement): W0 needs neighbour step17, while W1 has already sent step17 and is preparing step18. A late step16 packet may still be in the queue. Source comments say that message age and slot reuse are different checks. G rejects a mismatching epoch or step for the current boundary update and keeps the step17 slot live until acknowledged; the late packet does not become a valid step17 value. The notes do not specify whether every obsolete packet is discarded immediately or held for a later diagnostic, so do not invent that policy.

If matching input is absent beyond the existing timeout, all workers return to the last completed barrier snapshot and rerun from there using B. A partial G step is not reported as completed progress. The restart may cost time. The benchmark table includes ordinary polling/tag checks and waiting but none of the injected-timeout episodes below. No packet-loss rate or long-run failure probability is known.

## Recorded comparison protocol

results.csv holds 18 constructed records, one per case/mode. Within each case the same initial field, grid, partition plan, 2000 steps and floating-point precision are used. The reference is the serial execution of the same stencil. max_rel_error is the maximum relative field error at the final step; it is not a residual or speed metric. A row is eligible for the stated accuracy requirement if max_rel_error <= 1e-6. No repeats, standard deviations, confidence intervals or distributions were supplied. The fixed criteria were set before inspecting these constructed values.

elapsed_ms covers the advance loop, packing, queue polling, boundary checks and waits. It excludes one-off allocation/setup. peak_MiB includes the state and message buffers. G's extra storage is not automatically a fixed percentage of every grid size. Do not combine speed and error into an invented score. U's timings are still records and must not be deleted merely because errors violate the criterion.

balanced-small: 128×128 cells, comparable worker delay. balanced-large: 512×512 cells, comparable worker delay. skew-small/large use those sizes respectively, with W1 taking more interior work than the others. migration is 256×256 and changes the partition epoch midway. traffic-burst is 256×256 with clustered message delivery delays. Case names are categorical workloads, not a temporal trajectory. These constructed samples do not identify the precise hardware bottleneck.

## Separate fault checks

A replay of a prior-epoch message was refused in 12/12 constructed traces. A producer reaching two live slots waited in 12/12; it did not overwrite either. Suppressing the required neighbour packet triggered timeout and snapshot fallback in 4/4. Those traces establish intended branch behaviour only: they are not independent reliability trials or throughput measurements. In the 4 timeout cases the restarted B computation satisfied the final accuracy requirement, but elapsed time was not recorded. The single-buffer U failure is not remedied simply by storing a ready flag without matching epoch and step.

## Loose notes from the author

The implementation initially described all added functions equally. Packing and the update formula did not change. The release acknowledgement is required because writing step18 over a still-live step17 slot can defeat correct labelling. The epoch check matters when partition ownership changes. The tag match matters when neighbours do not advance together. None of these observations demonstrates a new diffusion equation, new discretization, universal scaling or optimal slot count. Figure sources need to be editable. Readers should be able to distinguish ownership, copied data, numerical step and actual flow without reading long box descriptions.
