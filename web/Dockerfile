FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json* /app/
RUN npm install || true
COPY . /app
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--port", "3000"]

