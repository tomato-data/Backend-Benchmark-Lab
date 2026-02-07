class HealthController < ApplicationController
  def show
    render json: { status: "ok", server: "ruby-rails" }
  end
end