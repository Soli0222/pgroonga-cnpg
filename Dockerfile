FROM groonga/pgroonga:4.0.5-alpine-18

USER root

# Change postgres user/group from UID/GID 70 to 26 (CNPG requirement)
# First remove tape group that uses GID 26
RUN delgroup tape && \
    deluser postgres && \
    addgroup -g 26 -S postgres && \
    adduser -u 26 -S -D -G postgres -H -h /var/lib/postgresql -s /bin/sh postgres && \
    chown -R postgres:postgres /var/lib/postgresql && \
    chown -R postgres:postgres /var/run/postgresql

USER 26
