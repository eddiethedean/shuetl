# Build context: this directory, with the frozen ShuETL and host wheels in wheels/.
# All roles use the same built image. The host wheel installs its trusted factory.
FROM python:3.12.13-slim-bookworm@sha256:4766d8b510c428e595d74b9cc5bbb2fae8e26316fffb4adc89908d79aacd58a2
COPY wheels/ /wheels/
RUN python -c 'import hashlib,json,pathlib; pathlib.Path("/usr/local/share/shuetl-wheels.json").write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path("/wheels").glob("*.whl")}))'
RUN python -m pip install --no-cache-dir "/wheels/shuetl-0.6.0-py3-none-any.whl[postgresql,server]" \
    /wheels/*host*.whl && python -m pip check \
    && useradd --uid 10001 --create-home shuetl && rm -r /wheels
USER 10001:10001
WORKDIR /home/shuetl
STOPSIGNAL SIGTERM
ENTRYPOINT ["python", "-m", "shuetl.cli"]
CMD ["serve", "--role", "gateway", "--host", "0.0.0.0", "--port", "8000"]
