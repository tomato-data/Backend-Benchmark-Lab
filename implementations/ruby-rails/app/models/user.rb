class User < ApplicationRecord
  self.table_name = "users"

  validates :name, presence: true, length: { maximum: 100 }
  validates :email, presence: true, uniqueness: true
end