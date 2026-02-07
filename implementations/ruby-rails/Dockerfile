FROM ruby:3.3-slim AS base

RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y \
    libpq5 libyaml-0-2 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

FROM base AS build

RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y \
    build-essential libpq-dev libyaml-dev && \
    rm -rf /var/lib/apt/lists/*

COPY Gemfile Gemfile.lock ./
RUN bundle config set --local deployment true && \
    bundle config set --local without 'development test' && \
    bundle install

COPY . .

FROM base

COPY --from=build /app /app
COPY --from=build /usr/local/bundle /usr/local/bundle

ENV RAILS_ENV=production
ENV RAILS_LOG_TO_STDOUT=true

EXPOSE 8000

CMD ["bundle", "exec", "puma", "-C", "config/puma.rb"]