import asyncio
import io
import json
import os
import random
import ssl
import threading
import uuid
import aiohttp
import requests
import websocket
from PIL import Image
from minio import S3Error
from .config import Config
from .loger import comfyui_loggerr
from .minioManager import MinioManager
from workFlows import workflows_json
from psd_tools import PSDImage
from .testing import Testing


class ComfyuiApi:
    def __init__(self, worktype, orderid, server_address="http://127.0.0.1:8188"):
        self.server_address = server_address
        self.work_type = worktype
        self.client_id = str(uuid.uuid4())
        self.ws_url = f"wss://{self.server_address.split("//")[1]}/ws?clientId={self.client_id}"
        self.upload_image_url = f"{self.server_address}/upload/image"
        self.orderid = orderid
        self.ws = None
        self.img_name_uuid_name_map = {}
        if workflows_json:

            # 更换背景
            self.cb_ab_nm_api = workflows_json['CB_AB_NM_API']      # 自动背景 无遮罩
            self.cb_mb_nm_api = workflows_json['CB_MB_NM_API']      # 手动背景 无遮罩
            self.cb_ab_m_api = workflows_json['CB_AB_M_API']        # 自动背景 有遮罩
            self.cb_mb_m_api = workflows_json['CB_MB_M_API']        # 手动背景 有遮罩

            # 一键抠图
            self.m_api = workflows_json['M_API']

            # 老照片修复
            self.pr_api = workflows_json['PR_API']

            # 扩图
            self.ep_api = workflows_json['EP_API']

            # 模特换装
            self.mc_api = workflows_json['MC_API']

    # 生成更换背景的工作流
    def genImagePrompt(self,getNumber,productName,maskName, backendName, mbackendName=''):
        '''
        获取生成图像的 prompt
        :param productName: 商品图
        :param backendName: 背景参考图
        :param mbackendName: 手动背景图
        :return: 完整的请求 JSON
        '''
        try:

            if maskName:
                if mbackendName:
                    newReqJson = self.cb_mb_m_api
                    newReqJson['412']['inputs']['image'] = mbackendName
                    comfyui_loggerr.info('use self.cb_mb_m_api')
                else:
                    newReqJson = self.cb_ab_m_api
                    comfyui_loggerr.info('use self.cb_ab_m_api')

                newReqJson['258']['inputs']['image'] = productName  # 填充参数
                if not mbackendName:
                    newReqJson['269']['inputs']['image'] = backendName
                newReqJson['102']['inputs']['seed'] = random.randint(10 ** 14, 10 ** 15 - 1)
                newReqJson['176']['inputs']['batch_size'] = getNumber
                # 添加遮罩
                newReqJson['228']['inputs']['image'] = maskName

            else:
                if mbackendName:
                    newReqJson = self.cb_mb_nm_api
                    newReqJson['412']['inputs']['image'] = mbackendName
                    comfyui_loggerr.info('use self.cb_mb_nm_api')
                else:
                    newReqJson = self.cb_ab_nm_api
                    comfyui_loggerr.info('use self.cb_ab_nm_api')

                newReqJson['258']['inputs']['image'] = productName  # 填充参数
                if not mbackendName:
                    newReqJson['269']['inputs']['image'] = backendName
                newReqJson['102']['inputs']['seed'] = random.randint(10**14, 10**15 - 1)
                newReqJson['176']['inputs']['batch_size'] = getNumber


            comfyui_loggerr.debug(f"Generated preview prompt for productName: {productName}")
            if maskName:
                comfyui_loggerr.debug(f"Generated preview prompt for maskName: {maskName}")
            if backendName:
                comfyui_loggerr.debug(f"Generated preview prompt for backendName: {backendName}")
            if mbackendName:
                comfyui_loggerr.debug(f"Generated preview prompt for mbackendName: {mbackendName}")


            return newReqJson
        except Exception as e:
            comfyui_loggerr.error(f"Failed to generate preview prompt: {str(e)}")
            return ''

    def genModChgPrompt(self, pdImg, mask, desc):
        try:
            if not pdImg or not mask:
                return ''

            newReqJson = self.mc_api
            comfyui_loggerr.info('use self.mc_api')
            newReqJson['14']['inputs']['image'] = pdImg
            newReqJson['96']['inputs']['image'] = mask
            newReqJson['38']['inputs']['string'] = desc['text']
            newReqJson['3']['inputs']['seed'] = random.randint(10 ** 14, 10 ** 15 - 1)
            comfyui_loggerr.debug(f"Generated preview prompt for productionImageName: {pdImg}")

            return newReqJson
        except Exception as e:
            comfyui_loggerr.error(f"Failed to generate preview prompt: {str(e)}")
            return ''


    # 抠图工作流
    def genMattingPrompt(self, pdImg):
        try:
            if not pdImg:
                return ''

            newReqJson = self.m_api
            comfyui_loggerr.info('use self.m_api')
            newReqJson['2']['inputs']['image'] = pdImg
            comfyui_loggerr.debug(f"Generated preview prompt for productionImageName: {pdImg}")

            return newReqJson
        except Exception as e:
            comfyui_loggerr.error(f"Failed to generate preview prompt: {str(e)}")
            return ''

    # 照片修复
    def genPicRstPrompt(self, pdImg):
        try:
            if not pdImg:
                return ''

            newReqJson = self.pr_api
            comfyui_loggerr.info('use self.pr_api')
            newReqJson['13']['inputs']['image'] = pdImg
            newReqJson['3']['inputs']['seed'] = random.randint(10 ** 14, 10 ** 15 - 1)
            comfyui_loggerr.debug(f"Generated preview prompt for productionImageName: {pdImg}")

            return newReqJson
        except Exception as e:
            comfyui_loggerr.error(f"Failed to generate preview prompt: {str(e)}")
            return ''

    # 照片扩图
    def genPicExpPrompt(self,pdImg, data):

        try:
            if not pdImg:
                return ''

            newReqJson = self.ep_api
            comfyui_loggerr.info('use self.ep_api')
            newReqJson['33']['inputs']['image'] = pdImg
            comfyui_loggerr.debug(f"Generated preview prompt for productionName: {pdImg}")

            newReqJson['40']['inputs']['seed'] = random.randint(10 ** 14, 10 ** 15 - 1)
            newReqJson['67']['inputs']['top'] = data['top']
            newReqJson['67']['inputs']['bottom'] = data['bottom']
            newReqJson['67']['inputs']['left'] = data['left']
            newReqJson['67']['inputs']['right'] = data['right']
            comfyui_loggerr.debug(f"Generated preview prompt for productionName arg: top:{data['top']},bottom:{data['bottom']},left:{data['left']},right:{data['right']} ")
            return newReqJson
        except Exception as e:
            comfyui_loggerr.error(f"Failed to generate preview prompt: {str(e)}")
            return ''


    # 响应时间多长需要设置
    async def get_image_data(self, session, url):
        try:
            timeout = aiohttp.ClientTimeout(total=Config.R_TIMEOUT)
            async with session.get(url,timeout=timeout) as response:
                if response.status == 200:
                    image_data = await response.read()
                    comfyui_loggerr.debug(f"Get image data from {url}")
                    return image_data
                else:
                    comfyui_loggerr.warning(f"Failed to get image data {url}, status: {response.status}")
                    return None
        except Exception as e:
            comfyui_loggerr.error(f"Error Get image data from {url}: {e}")
            return None

    async def process_and_save_image(self, image_data, filename, output_dir):
        try:
            comfyui_loggerr.debug(f"Processing image: {filename}")
            if filename.lower().endswith('.psd'):
                file_bytes = io.BytesIO(image_data)
                psd = PSDImage.open(file_bytes)
                # 保存修改后的 PSD 文件
                image_path = os.path.join(output_dir, filename)
                # 使用 psd_tools 保存文件
                with open(image_path, 'wb') as f:
                    psd.save(f)
                comfyui_loggerr.debug(f"Image saved to {image_path}")

            else:
                image = Image.open(io.BytesIO(image_data))
                image_path = os.path.join(output_dir, filename)
                image.save(image_path)
                comfyui_loggerr.debug(f"Image saved to {image_path}")
            return image_path
        except Exception as e:
            comfyui_loggerr.error(f"Error processing and saving image {filename}: {e}")
            return None

    async def upload_image_sd(self, session, image_path):
        try:
            comfyui_loggerr.debug(f"Start Uploading image: {image_path}")
            with open(image_path, 'rb') as f:
                data = {'image': f}
                timeout = aiohttp.ClientTimeout(total=Config.R_TIMEOUT)
                async with session.post(self.upload_image_url,timeout=timeout, data=data, ssl=False) as response:
                    if response.status == 200:
                        comfyui_loggerr.debug(f"Image uploaded Comfyui successfully: {image_path}")
                        return True
                    else:
                        comfyui_loggerr.warning(f"Failed to upload {image_path}, status: {response.status}")
                        return False
        except Exception as e:
            comfyui_loggerr.error(f"Error uploading image {image_path}: {e}")
            return False

    async def handle_url(self, session, url, output_dir):
        if not url:
            comfyui_loggerr.warning("No URL provided, skipping...")
            return ""

        try:
            filename = os.path.basename(url)
            if filename.lower().split('.')[-1] not in Config.IMG_FORMAT:
                comfyui_loggerr.warning(f"Unsupported file type for URL: {url}")
                return ""
            image_data = await self.get_image_data(session, url)
            if not image_data:
                return ""

            image_path = await self.process_and_save_image(image_data, filename, output_dir)
            if not image_path:
                return ""

            upload_success = await self.upload_image_sd(session, image_path)
            if upload_success:
                return filename
            else:
                return ""
        except Exception as e:
            comfyui_loggerr.error(f"Error handling URL {url}: {e}")
            return ""

    async def d_u_images(self, urls, output_dir):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            comfyui_loggerr.debug(f"output directory create: {output_dir}")
        else:
            comfyui_loggerr.debug(f"output directory exists: {output_dir}")

        # 设置timeout时长
        timeout = aiohttp.ClientTimeout(total=Config.R_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            tasks = [self.handle_url(session, url, output_dir) for url in urls]
            results = await asyncio.gather(*tasks)
            comfyui_loggerr.debug("Image download and upload tasks completed.")

            return results

    def queue_prompt(self, prompt):
        data = {
            "prompt": prompt,
            "client_id": self.client_id
        }

        try:
            comfyui_loggerr.debug(f"Sending POST request")
            response = requests.post(f"{self.server_address}/prompt", json=data)
            response.raise_for_status()
            comfyui_loggerr.debug("POST request sent successfully.")
            return response.json()
        except requests.exceptions.RequestException as e:
            comfyui_loggerr.error(f"Failed to send POST request: {e}")
            self.response_service(status=2, remarks=f"Failed to send POST request: {e}")
            return None

    def connect(self):
        try:
            comfyui_loggerr.debug(f"Connecting to WebSocket at {self.ws_url}")
            # 跳过ssl验证
            self.ws = websocket.WebSocket(sslopt={"cert_reqs": ssl.CERT_NONE})
            self.ws.connect(self.ws_url)
            comfyui_loggerr.debug("WebSocket connection established.")
        except Exception as e:
            comfyui_loggerr.error(f"Failed to establish WebSocket connection: {e}")
            self.ws = None


    async def process_and_download(self, out_image_name):
        """下载所有图像并按 node_num 分组"""
        # print(out_image_name)
        # comfyui_loggerr.debug(f"Starting to process {len(out_image_name[list(out_image_name.keys())[0]])} images.")


        # # 存储所有下载的图像路径
        download_results = {key: [] for key in out_image_name}

        tasks = []

        for node_num in out_image_name.keys():
            for img_info in out_image_name[node_num]:
                tasks.append(self.download_image( node_num, img_info['filename'], img_info['type'], download_results))

        # 等待所有下载任务完成
        await asyncio.gather(*tasks)
        comfyui_loggerr.debug(f"Downloaded all images. Proceeding to upload. Downloaded images: {download_results}")

        # 判断download_results的数量是不是符合 符合返回正常值
        # 直接判断字典结构和元素数量
        if download_results.keys() == out_image_name.keys():
            # 如果键相同，检查每个键对应的值的数量是否一致
            mark = True
            for key in download_results:
                if len(download_results[key]) != len(out_image_name[key]):
                    mark = False
                    break
            if mark:
                return download_results
            else:
                return ''

        else:
            return ''


    async def download_image(self, node_num, filename, filetype, d_results):
        """下载单个图像并保存到本地"""
        url = f"{self.server_address}/view?filename={filename}&type={filetype}"
        comfyui_loggerr.debug(f"Preparing to download image {filename} of type {filetype} from {url}")

        try:
            # 使用 aiohttp 客户端下载图像
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=False) as response:
                    response.raise_for_status()  # 确保请求成功
                    comfyui_loggerr.debug(f"Successfully downloaded image: {filename}")

                    # print(f'download_image() self.work_type = {self.work_type} ')
                    match self.work_type:
                        case Config.GEN_IMAGE:
                            # 根据 image_id 确定保存路径
                            if node_num == '414':
                                uuid_name_png = str(uuid.uuid4()) + '.png'
                                comfyui_loggerr.debug(f"{filename} change for {uuid_name_png}")
                                self.img_name_uuid_name_map[filename] = uuid_name_png
                                img_path = os.path.join(Config.IMAGES_TMP, uuid_name_png)
                            elif node_num == '415':
                                uuid_name_tmp_png = str(uuid.uuid4()) + '.png'
                                comfyui_loggerr.debug(f"{filename} change for {uuid_name_tmp_png}")
                                self.img_name_uuid_name_map[filename] = uuid_name_tmp_png
                                img_path = os.path.join(Config.IMAGES_TMP, uuid_name_tmp_png)
                            else:
                                comfyui_loggerr.error(f"Unexpected GEN_IMAGE image_id {node_num}.")
                                self.response_service(status=2, remarks=f"Unexpected GEN_IMAGE image_id {node_num}")
                                return None

                        case Config.GEN_MANEQUIN:
                            if node_num == '194':
                                uuid_name_png = str(uuid.uuid4()) + '.png'
                                comfyui_loggerr.debug(f"{filename} change for {uuid_name_png}")
                                self.img_name_uuid_name_map[filename] = uuid_name_png
                                img_path = os.path.join(Config.IMAGES_TMP, uuid_name_png)

                            else:
                                comfyui_loggerr.error(f"Unexpected GEN_MANEQUIN image_id {node_num}.")
                                self.response_service(status=2, remarks=f"Unexpected GEN_MANEQUIN image_id {node_num}")
                                return None



                        case Config.GEN_PICRST:
                            if node_num == '9':
                                uuid_name_png = str(uuid.uuid4()) + '.png'
                                comfyui_loggerr.debug(f"{filename} change for {uuid_name_png}")
                                self.img_name_uuid_name_map[filename] = uuid_name_png
                                img_path = os.path.join(Config.IMAGES_TMP, uuid_name_png)
                            else:
                                comfyui_loggerr.error(f"Unexpected GEN_PICRST image_id {node_num}.")
                                self.response_service(status=2, remarks=f"Unexpected GEN_PICRST image_id {node_num}")
                                return None

                        case Config.GEN_MATTING:
                            if node_num == '12':
                                uuid_name_png = str(uuid.uuid4()) + '.png'
                                comfyui_loggerr.debug(f"{filename} change for {uuid_name_png}")
                                self.img_name_uuid_name_map[filename] = uuid_name_png
                                img_path = os.path.join(Config.IMAGES_TMP, uuid_name_png)
                            elif node_num == '13':
                                uuid_name_tmp_png = str(uuid.uuid4()) + '.png'
                                comfyui_loggerr.debug(f"{filename} change for {uuid_name_tmp_png}")
                                self.img_name_uuid_name_map[filename] = uuid_name_tmp_png
                                img_path = os.path.join(Config.IMAGES_TMP, uuid_name_tmp_png)
                            else:
                                comfyui_loggerr.error(f"Unexpected GEN_MATTING image_id {node_num}.")
                                self.response_service(status=2, remarks=f"Unexpected GEN_MATTING image_id {node_num}")
                                return None


                        case Config.GEN_EXPIC:
                            if node_num == '59':
                                uuid_name_png = str(uuid.uuid4()) + '.png'
                                comfyui_loggerr.debug(f"{filename} change for {uuid_name_png}")
                                self.img_name_uuid_name_map[filename] = uuid_name_png
                                img_path = os.path.join(Config.IMAGES_TMP, uuid_name_png)

                            else:
                                comfyui_loggerr.error(f"Unexpected GEN_EXPIC image_id {node_num}.")
                                self.response_service(status=2, remarks=f"Unexpected GEN_EXPIC image_id {node_num}")
                                return None


                        case _:
                            comfyui_loggerr.error(f"Unknown workerType value: {self.work_type}")
                            self.response_service(status=2, remarks=f"Unknown workerType value: {self.work_type}")
                            return

                            # 保存图像到本地
                    with open(img_path, "wb") as file:
                        file.write(await response.read())
                    comfyui_loggerr.debug(f"Image saved to local path: {img_path}")

                    # 将下载的文件路径加入到结果字典
                    d_results[node_num].append(img_path)

                    return d_results

        except Exception as e:
            comfyui_loggerr.error(f"Failed to download image '{filename}': {str(e)}")
            self.response_service(status=2, remarks=f"Failed to download image '{filename}': {str(e)}")
            return None


    async def upload_images_to_minio(self, download_results):
        """批量上传下载的图像到 MinIO"""
        comfyui_loggerr.debug(f"after get img from comfyui and upload to MinIO.")

        result_list = []

        upload_minio = MinioManager(Config.MINIO_URL, Config.MINIO_ROOT_USER, Config.MINIO_ROOT_PASSWORD)

        try:
            # 创建 bucket（如果不存在）
            upload_minio.create_bucket(Config.GENERATED_MINIO_BUCKET_NAME)
            upload_minio.create_bucket(Config.GENERATED_TMP_MINIO_BUCKET_NAME)

            # 按 node_num 分批上传
            for node_num, img_paths in download_results.items():
                for img_path in img_paths:
                    obj_name = os.path.basename(img_path)
                    comfyui_loggerr.debug(f"Uploading file {obj_name} to MinIO")

                    match self.work_type:
                        case Config.GEN_IMAGE:
                            if node_num == '414':
                                upload_minio.upload_file(Config.GENERATED_MINIO_BUCKET_NAME, obj_name, img_path,
                                                         content_type='image/png')
                                comfyui_loggerr.info(
                                    f"Image uploaded to MinIO bucket {Config.GENERATED_MINIO_BUCKET_NAME}: {obj_name}")

                                result_list.append(obj_name)
                            elif node_num == '415':
                                upload_minio.upload_file(Config.GENERATED_TMP_MINIO_BUCKET_NAME, obj_name, img_path,
                                                         content_type='image/png')
                                comfyui_loggerr.info(
                                    f"Image uploaded to MinIO bucket {Config.GENERATED_TMP_MINIO_BUCKET_NAME}: {obj_name}")

                                result_list.append(obj_name)
                            else:
                                comfyui_loggerr.warning(f"Unexpected GEN_IMAGE image_id {node_num}.")
                                self.response_service(status=2, remarks=f"Unexpected GEN_IMAGE image_id {node_num}")
                                return ''

                        case Config.GEN_MANEQUIN:
                            if node_num == '194':
                                upload_minio.upload_file(Config.GENERATED_MINIO_BUCKET_NAME, obj_name, img_path,
                                                         content_type='image/png')
                                comfyui_loggerr.info(
                                    f"Image uploaded to MinIO bucket {Config.GENERATED_MINIO_BUCKET_NAME}: {obj_name}")

                                result_list.append(obj_name)
                            else:
                                comfyui_loggerr.warning(f"Unexpected GEN_MANEQUIN image_id {node_num}.")
                                self.response_service(status=2, remarks=f"Unexpected GEN_MANEQUIN image_id {node_num}")
                                return ''




                        case Config.GEN_PICRST:
                            if node_num == '9':
                                upload_minio.upload_file(Config.GENERATED_MINIO_BUCKET_NAME, obj_name, img_path,
                                                         content_type='image/png')
                                comfyui_loggerr.info(
                                    f"Image uploaded to MinIO bucket {Config.GENERATED_MINIO_BUCKET_NAME}: {obj_name}")

                                result_list.append(obj_name)
                            else:
                                comfyui_loggerr.warning(f"Unexpected GEN_PICRST image_id {node_num}.")
                                self.response_service(status=2, remarks=f"Unexpected GEN_PICRST image_id {node_num}")
                                return ''


                        case Config.GEN_MATTING:
                            if node_num == '12':
                                upload_minio.upload_file(Config.GENERATED_MINIO_BUCKET_NAME, obj_name, img_path,
                                                         content_type='image/png')
                                comfyui_loggerr.info(
                                    f"Image uploaded to MinIO bucket {Config.GENERATED_MINIO_BUCKET_NAME}: {obj_name}")

                                result_list.append(obj_name)
                            elif node_num == '13':
                                upload_minio.upload_file(Config.GENERATED_TMP_MINIO_BUCKET_NAME, obj_name, img_path,
                                                         content_type='image/png')
                                comfyui_loggerr.info(
                                    f"Image uploaded to MinIO bucket {Config.GENERATED_TMP_MINIO_BUCKET_NAME}: {obj_name}")

                                result_list.append(obj_name)
                            else:
                                comfyui_loggerr.warning(f"Unexpected GEN_MATTING image_id {node_num}.")
                                self.response_service(status=2, remarks=f"Unexpected GEN_MATTING image_id {node_num}")
                                return ''

                        case Config.GEN_EXPIC:
                            if node_num == '59':
                                upload_minio.upload_file(Config.GENERATED_MINIO_BUCKET_NAME, obj_name, img_path,
                                                         content_type='image/png')
                                comfyui_loggerr.info(
                                    f"Image uploaded to MinIO bucket {Config.GENERATED_MINIO_BUCKET_NAME}: {obj_name}")

                                result_list.append(obj_name)
                            else:
                                comfyui_loggerr.warning(f"Unexpected GEN_MATTING image_id {node_num}.")
                                self.response_service(status=2, remarks=f"Unexpected GEN_MATTING image_id {node_num}")
                                return ''

                        case _:
                            comfyui_loggerr.error(f"Unknown workerType value: {self.work_type}")
                            self.response_service(status=2, remarks=f"Unknown workerType value: {self.work_type}")
                            return

            return result_list

        except S3Error as e:
            comfyui_loggerr.error(f"Failed to upload images to MinIO: {str(e)}")
            self.response_service(status=2, remarks=f"Failed to upload images to MinIO: {str(e)}")
            return ''

    async def d_from_sd_u_minio(self, out_image_dict):
        """下载所有图像并批量上传到 MinIO"""
        comfyui_loggerr.debug(f"starting to download images from Comfyui.")

        # 步骤1：先下载所有图像
        download_results = await self.process_and_download(out_image_dict)

        if download_results == '':
            self.response_service(status=2, remarks=f"Download from comfyui error")
            return ''

        # 步骤2：批量上传图像到 MinIO
        upload_results = await self.upload_images_to_minio(download_results)

        if upload_results:
            return upload_results
        else:
            return ''


    def response_service(self,status=1, share_fullpath="", share_halfpath="",remarks=""):
        # 构造POST请求的数据
        post_data = {
            "orderid": self.orderid,
            "status": status,
            "fullpath": share_fullpath,
            "halfpath": share_halfpath,  # 如果有半路径需求可以填入
            "pass": 'ai2024',
            "remarks": remarks
        }

        try:
            # 发送POST请求
            response = requests.post(Config.SHARE_RES_API, json=post_data)
            response.raise_for_status()  # 确保请求成功
            comfyui_loggerr.info(f"Share response sent successfully for orderID :{self.orderid}")
        except requests.exceptions.RequestException as e:
            comfyui_loggerr.error(f"Error sending share request for {self.orderid}: {str(e)}")

    @Testing.timing_use
    def _execute_task(self, prompt):
        out_image_name = {}  # {"414":[], "415":[]}
        self.connect()
        if not self.ws:
            comfyui_loggerr.error("WebSocket connection failed. Exiting task.")
            self.response_service(status=2,remarks="WebSocket connection failed. Exiting task.")
            return

        prompt_data = self.queue_prompt(prompt)
        if not prompt_data:
            comfyui_loggerr.error("Failed to queue prompt. Exiting task.")
            self.response_service(status=2, remarks="Failed to queue prompt. Exiting task.")
            return

        prompt_id = prompt_data.get('prompt_id')
        comfyui_loggerr.info(f"Received prompt_id: {prompt_id}")

        # 根据websocket 提取数据
        try:
            while True:
                out = self.ws.recv()
                # 有时候会传输二进制文件
                if isinstance(out, str):
                    comfyui_loggerr.debug(f"Received WebSocket data: {out}")
                    message = json.loads(out)
                    if message['type'] == 'executing':
                        data = message['data']
                        if data['prompt_id'] == prompt_id:
                            if data['node'] is None:
                                break  # Execution is done
                    if message['type'] == 'execution_error':
                        out_image_name = {}
                        data = message['data']
                        comfyui_loggerr.error(f'workflow execution_error exception_type {data['exception_type']}')
                        self.response_service(status=2, remarks=f'workflow execution_error exception_type {data['exception_type']}')
                        break

                    if message['type'] == 'execution_interrupted':
                        out_image_name = {}
                        data = message['data']
                        comfyui_loggerr.error(f'workflow execution_interrupted node_type {data['node_type']}')
                        self.response_service(status=2, remarks=f'workflow execution_interrupted node_type {data['node_type']}')
                        break

                    # 根据上传类型处理 生成的图片
                    match self.work_type:
                        case Config.GEN_IMAGE:
                            if message.get('type') == 'executed':
                                data = message['data']
                                if data['node'] == '414' and data['prompt_id'] == prompt_id:
                                    imgs = data['output']['images']
                                    out_image_name['414'] = imgs
                                    comfyui_loggerr.debug(f"Image generated: {imgs}")

                            if message.get('type') == 'early-image-handler':
                                data = message['data']
                                if data['id'] == '415':
                                    imgs = data['urls']  #是个列表[]
                                    out_image_name['415'] = imgs
                                    comfyui_loggerr.debug(f"TMP Image generated: {imgs}")
                        case Config.GEN_MANEQUIN:
                            if message.get('type') == 'executed':
                                data = message['data']
                                if data['node'] == '194' and data['prompt_id'] == prompt_id:
                                    imgs = data['output']['images']
                                    out_image_name['194'] = imgs
                                    comfyui_loggerr.debug(f"Image generated: {imgs}")

                        case Config.GEN_PICRST:
                            if message.get('type') == 'executed':
                                data = message['data']
                                if data['node'] == '9' and data['prompt_id'] == prompt_id:
                                    imgs = data['output']['images']
                                    out_image_name['9'] = imgs
                                    comfyui_loggerr.debug(f"Image generated: {imgs}")

                        case Config.GEN_MATTING:
                            if message.get('type') == 'executed':
                                data = message['data']
                                if data['node'] == '12' and data['prompt_id'] == prompt_id:
                                    imgs = data['output']['images']
                                    out_image_name['12'] = imgs
                                    comfyui_loggerr.debug(f"Image generated: {imgs}")

                                if data['node'] == '13' and data['prompt_id'] == prompt_id:
                                    imgs = data['output']['images']
                                    out_image_name['13'] = imgs
                                    comfyui_loggerr.debug(f"Image generated: {imgs}")

                        case Config.GEN_EXPIC:
                            if message.get('type') == 'executed':
                                data = message['data']
                                if data['node'] == '59' and data['prompt_id'] == prompt_id:
                                    imgs = data['output']['images']
                                    out_image_name['59'] = imgs
                                    comfyui_loggerr.debug(f"Image generated: {imgs}")

                        case _:
                            comfyui_loggerr.error(f"Unknown workerType value: {self.work_type}")
                            self.response_service(status=2, remarks=f"Unknown workerType value: {self.work_type}")
                            return

        except Exception as e:
            comfyui_loggerr.error(f"Error while receiving WebSocket data: {e}")
            self.response_service(status=2, remarks=f"Error while receiving WebSocket data: {e}")
            return

        finally:
            if self.ws:
                self.ws.close()
                comfyui_loggerr.debug("WebSocket connection closed.")

        comfyui_loggerr.debug(f"out_image_name-> {out_image_name}")

        if not out_image_name:
            return


        try:
            # 处理 out_image_name 生成图的下载到本地与上传到minio
            """{'415': [
                        {'filename': 'ComfyUI_temp_akgkr_00001_.png', 'subfolder': '', 'type': 'temp'},
                        {'filename': 'ComfyUI_temp_akgkr_00002_.png', 'subfolder': '', 'type': 'temp'},
                        {'filename': 'ComfyUI_temp_akgkr_00003_.png', 'subfolder': '', 'type': 'temp'},
                        {'filename': 'ComfyUI_temp_akgkr_00004_.png', 'subfolder': '', 'type': 'temp'}
                       ],
                '414': [
                        {'filename': 'ComfyUI_00058_.png', 'subfolder': '', 'type': 'output'},
                        {'filename': 'ComfyUI_00059_.png', 'subfolder': '', 'type': 'output'}, 
                        {'filename': 'ComfyUI_00060_.png', 'subfolder': '', 'type': 'output'}, 
                        {'filename': 'ComfyUI_00061_.png', 'subfolder': '', 'type': 'output'}]
                }
            """

            """ output_dict
             {'415': ['ComfyUI_temp_akgkr_00001_.png', 'ComfyUI_temp_akgkr_00002_.png', 'ComfyUI_temp_akgkr_00003_.png', 'ComfyUI_temp_akgkr_00004_.png'], 
              '414': ['ComfyUI_00058_.png', 'ComfyUI_00059_.png', 'ComfyUI_00060_.png', 'ComfyUI_00061_.png']}
            """
            output_dict = {key: [item['filename'] for item in value] for key, value in out_image_name.items()}

            minio_img = asyncio.run(self.d_from_sd_u_minio(out_image_name))

            if minio_img:
                # 替换映射表的内容
                obj_name = {key: [self.img_name_uuid_name_map[file] for file in file_list] for key, file_list in output_dict.items()}
                comfyui_loggerr.debug(f'ready minio images: {obj_name}')


                if obj_name:
                    # 构造分享 URL
                    share_fullpath = []
                    share_halfpath = []
                    for k in obj_name.keys():
                        for img_name in obj_name[k]:
                            match self.work_type:
                                case Config.GEN_IMAGE:
                                    if k == '414':
                                        img_name = Config.SHARE_MINIO_URL_PRX + img_name
                                        share_fullpath.append(img_name)
                                    if k == '415':
                                        img_name = Config.SHARE_MINIO_URL_TMP_PRX + img_name
                                        share_halfpath.append(img_name)

                                case Config.GEN_MANEQUIN:
                                    if k == '194':
                                        img_name = Config.SHARE_MINIO_URL_PRX + img_name
                                        share_fullpath.append(img_name)

                                case Config.GEN_PICRST:
                                    if k == '9':
                                        img_name = Config.SHARE_MINIO_URL_PRX + img_name
                                        share_fullpath.append(img_name)

                                case Config.GEN_MATTING:
                                    if k == '12':
                                        img_name = Config.SHARE_MINIO_URL_PRX + img_name

                                        share_fullpath.append(img_name)
                                        share_halfpath.append(img_name)
                                    if k == '13':

                                        img_name = Config.SHARE_MINIO_URL_TMP_PRX + img_name
                                        share_fullpath.append(img_name)
                                        share_halfpath.append(img_name)

                                case Config.GEN_EXPIC:
                                    if k == '59':
                                        img_name = Config.SHARE_MINIO_URL_PRX + img_name
                                        share_fullpath.append(img_name)

                                case _:
                                    comfyui_loggerr.error(f"Unknown workerType value: {self.work_type}")
                                    self.response_service(status=2, remarks=f"Unknown workerType value: {self.work_type}")
                                    return

                    print(f'share_fullpath - {share_fullpath}')
                    print(f'share_halfpath - {share_halfpath}')
                    # 成功响应服务器
                    self.response_service(share_fullpath=share_fullpath,share_halfpath=share_halfpath)

            else:
                comfyui_loggerr.error(f"Failed to upload image to Minio")
                self.response_service(status=2, remarks=f"Failed to upload image to Minio")
                return ''

        except requests.exceptions.RequestException as e:
            comfyui_loggerr.error(f"Error during final steps: {e}")
            self.response_service(status=2, remarks=f"Error during final steps: {e}")
            return ''


    def create_work(self, prompt):
        comfyui_loggerr.debug(f"Starting thread to execute task for prompt")
        task_thread = threading.Thread(target=self._execute_task, args=(prompt, ))
        task_thread.start()
        comfyui_loggerr.debug("Task thread started.")
