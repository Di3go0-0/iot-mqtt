FROM node:20-slim

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY tsconfig.json ./
COPY src/ ./src/
COPY views/ ./views/
COPY public/ ./public/

RUN npm run build

CMD ["node", "dist/index.js"]
