# Use an official Node.js runtime as a parent image
FROM node:20-alpine

WORKDIR /usr/src/app

COPY package*.json ./

RUN npm install

COPY . .

RUN npm run build


EXPOSE 3020

CMD [ "node", "dist/cli.js" ]
