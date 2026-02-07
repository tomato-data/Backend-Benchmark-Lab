Rails.application.routes.draw do
  get "health", to: "health#show"
  post "echo", to: "echo#create"
  get "users", to: "users#index"
  post "users", to: "users#create"
  get "users/:id", to: "users#show"
  get "external", to: "external#show"
  get "protected", to: "protected#show"
  post "upload", to: "upload#create"
end
