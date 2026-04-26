defmodule OampTypes.MixProject do
  use Mix.Project

  @version "1.0.1"

  def project do
    [
      app: :oamp_types,
      version: @version,
      elixir: "~> 1.14",
      start_permanent: Mix.env() == :prod,
      deps: deps(),
      description: "Elixir types for the Open Agent Memory Protocol (OAMP) v1",
      package: [
        name: "oamp_types",
        licenses: ["MIT"],
        links: %{
          "GitHub" => "https://github.com/deep-thinking-llc/open-agent-memory-protocol"
        }
      ]
    ]
  end

  def application do
    [
      extra_applications: [:logger]
    ]
  end

  defp deps do
    [
      {:jason, "~> 1.4"},
      {:ex_doc, "~> 0.34", only: :dev, runtime: false}
    ]
  end
end