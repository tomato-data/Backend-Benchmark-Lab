class UploadController < ApplicationController
  def create
    file = params[:file]

    if file.blank?
      return render json: { detail: "No file uploaded" }, status: :bad_request
    end

    render json: {
      filename: file.original_filename,
      size: file.size,
      content_type: file.content_type
    }
  end
end