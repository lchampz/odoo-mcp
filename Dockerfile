FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir uv

COPY pyproject.toml .
COPY src/ src/

RUN uv pip install --system --no-cache .

ENV ODOO_URL=""
ENV ODOO_DATABASE=""
ENV ODOO_USERNAME=""
ENV ODOO_PASSWORD=""

EXPOSE 8000

CMD ["odoo-crm-mcp", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000"]
