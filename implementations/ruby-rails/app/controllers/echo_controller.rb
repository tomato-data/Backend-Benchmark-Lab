class EchoController < ApplicationController
  def create
    render json: request.raw_post.present? ? JSON.parse(request.raw_post) : {}
  end
end