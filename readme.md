# QQ图片机器人

基于
[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)
和
[Stable Diffusion](https://github.com/AUTOMATIC1111/stable-diffusion-webui)
制作的QQ机器人，用于使用简单方式生成图片。

***

## 介绍

QQ的信息时间和消息发送使用go-http服务，图片生成使用python服务，两者通过http请求通讯。

图片生成服务由Stable Diffusion webui的API提供，同样通过http请求通讯。

图片审查模型使用[nsfw_model](https://github.com/GantMan/nsfw_model)

## 已实现的功能

抓取特定关键字（listener.py)，解析关键字(message.py)，请求SD生成图片(sd_api.py)，缓存图片至本地（支持多个图片），图片审查，发送图片