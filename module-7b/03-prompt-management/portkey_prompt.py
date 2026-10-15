# Example usage of the Prompts written in Portkey and executing them code copied from Portkey itself from prompts -->prompts template -->view code

from portkey_ai import Portkey

client = Portkey(
    base_url="https://api.portkey.ai/v1",
    api_key="jtpGvJkpclnQ4p4hf10vx2HxAwda"  # defaults to os.environ.get("PORTKEY_API_KEY")
)

# Make the prompt creation call with the variables
prompt_completion = client.prompts.completions.create(
    prompt_id="pp-adding-pro-6d775b",
    variables={}
)

# Make the prompt creation call with the variables - stream mode
stream_prompt_completion = client.prompts.completions.create(
    prompt_id="pp-adding-pro-6d775b",
    variables={},
    stream=True
)
