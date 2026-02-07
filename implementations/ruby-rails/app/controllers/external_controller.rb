class ExternalController < ApplicationController
  def show
    start = Process.clock_gettime(Process::CLOCK_MONOTONIC)

    sleep(0.1)

    latency = ((Process.clock_gettime(Process::CLOCK_MONOTONIC) - start) * 1000).round(2)

    render json: {
      source: "simulated_external_api",
      latency_ms: latency,
      data: { message: "External API response" }
    }
  end
end