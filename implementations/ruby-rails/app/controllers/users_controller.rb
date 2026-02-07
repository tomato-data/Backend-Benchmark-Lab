class UsersController < ApplicationController
  # GET /users
  def index
    users = User.all.limit(100)
    render json: users, only: [:id, :name, :email, :created_at]
  end

  # POST /users
  def create
    user = User.new(user_params)

    if user.save
      render json: user, only: [:id, :name, :email, :created_at], status: :created
    else
      render json: { errors: user.errors.full_messages }, status: :unprocessable_entity
    end
  end

  # GET /users/:id
  def show
    user = User.find(params[:id])
    render json: user, only: [:id, :name, :email, :created_at]
  rescue ActiveRecord::RecordNotFound
    render json: { detail: "Not found" }, status: :not_found
  end

  private

  def user_params
    params.expect(user: [:name, :email])
  end
end