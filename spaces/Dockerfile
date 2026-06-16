FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

# Install directly from PyPI — always uses the latest published version
RUN uv pip install --system --no-cache odoo-crm-mcp

ENV ODOO_URL=""
ENV ODOO_DATABASE=""
ENV ODOO_USERNAME=""
ENV ODOO_PASSWORD=""

# HuggingFace Spaces uses port 7860
EXPOSE 7860

CMD odoo-crm-mcp --transport streamable-http --host 0.0.0.0 --port 7860
