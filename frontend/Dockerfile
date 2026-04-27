FROM node:22-alpine

WORKDIR /app

COPY package.json ./
RUN rm -f package-lock.json && npm install

COPY . .

CMD ["npm", "run", "dev"]
