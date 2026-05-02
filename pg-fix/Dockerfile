FROM postgres:18

COPY start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

ENV PGDATA=/var/lib/postgresql/data/pgdata

CMD ["/usr/local/bin/start.sh"]

