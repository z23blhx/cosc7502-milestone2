# Retained setup failures

No performance samples from these jobs enter analysis.

- 623293:baseline profiling stopped on an unsupported diagnostic option.
- 623304:20-minute request exceeded the course QoS15-minute cap; cancelled
 before execution. There is no Slurm stdout because it never ran.
- 623305:filename-bearing diagnostic syntax still rejected by GCC8.
- 623306:expanded correctness tests passed; diagnostic command then failed.

The raw compiler messages and accounting are retained. Redirecting diagnostics
from stderr instead of using filename-bearing options fixed the compiler-report
failure. Fifteen-minute scripts fixed the resource-policy rejection. Neither
failure was a simulation deadlock or incorrect result.
