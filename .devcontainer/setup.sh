echo "Setting up devcontainer..."
echo "Installing pre-commit hooks..."
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync --frozen
uv run pre-commit install
echo "Setting up devcontainer complete."