Packaging dependencies:

1. Unpack and enter sources directory.
2. `mvn -B dependency:go-offline -Dmaven.repo.local=repository`
3. `tar --zstd -cvf onedev-server-deps.tar.zst repository`
