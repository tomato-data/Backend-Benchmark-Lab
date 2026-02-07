class ProtectedController < ApplicationController
  def show
    authorization = request.headers["Authorization"]

    if authorization.blank?
      return render json: { detail: "Authorization header required" }, status: :unauthorized
    end

    unless authorization.start_with?("Bearer ")
      return render json: { detail: "Invalid authorization format" }, status: :unauthorized
    end

    token = authorization.delete_prefix("Bearer ")

    if token.length < 10
      return render json: { detail: "Invalid token" }, status: :unauthorized
    end

    render json: {
      message: "Access granted",
      user: "user_from_token_#{token[0, 8]}"
    }
  end
end