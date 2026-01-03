FROM node:22-alpine

WORKDIR /app

# 의존성 설치
COPY package*.json ./
RUN npm ci

# Prisma 설정 복사 및 generate
COPY prisma ./prisma/
COPY prisma.config.ts ./

# 빌드 시점에만 사용되는 더미 URL (generate만 하면 됨)
ENV DATABASE_URL="postgresql://dummy:dummy@localhost:5432/dummy"
RUN npx prisma generate

# 소스 복사
COPY tsconfig.json ./
COPY src ./src/

# 빌드
RUN npm run build

EXPOSE 8000

CMD ["node", "dist/app.js"]