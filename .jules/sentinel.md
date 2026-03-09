## 2026-03-09 - [Argument Injection in Nmap Recon Agent]
**Vulnerability:** Lack of input validation on the 'target' parameter allowed arbitrary strings to be passed to the `nmap` command, potentially leading to argument injection or command execution depending on the underlying `python-nmap` implementation and shell usage.
**Learning:** Security tools themselves (like Nmap) can be a vector for attack if user input is not strictly validated before being passed as arguments.
**Prevention:** Implement strict allow-list validation for hostnames and IP addresses using regular expressions and standard library functions (e.g., `socket.inet_aton`).

## 2026-03-09 - [Information Leakage in API Error Responses]
**Vulnerability:** The API was returning raw exception messages (`str(e)`) to the client, which could leak internal path details, database structure, or other sensitive information.
**Learning:** Defaulting to returning error messages in development might be helpful, but it's a security risk in production-like agents.
**Prevention:** Catch all top-level exceptions and return a generic, non-informative error message to the user while logging the full details internally for debugging.
