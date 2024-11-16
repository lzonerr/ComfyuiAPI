import asyncio
import requests
import validators
from flask import Blueprint, request
from comfyui_web.comfyuiApi import ComfyuiApi
from .config import Config
from .helper import success_response, error_response
from .loger import comfyui_loggerr

comfyui_bp = Blueprint('main', __name__)

@comfyui_bp.route('/api/outer/gimage', methods=['POST'])
def gen_image():
    comfyui_loggerr.debug("gen_image api endpoint called - Start")

    try:
        # 获取请求数据并转为 JSON 格式
        req_json = request.get_json()
        if req_json is None:
            comfyui_loggerr.error("Invalid request: No JSON data found")
            return error_response("No JSON data found")

        comfyui_loggerr.debug(f"Request data received: {req_json}")

        # 获取请求类型
        get_type = req_json.get('workerType')
        if not get_type:
            comfyui_loggerr.error("Invalid request: 'workerType' is required")
            return error_response("'workerType' is required")

        # 处理不同的 workerType 类型 1：背景换图 2：模特换装等
        match get_type:
            case Config.GEN_IMAGE:
                comfyui_loggerr.info("Processing GEN_IMAGE logic")
                order_id = req_json['orderid']
                dev_url = req_json.get('devUrl')
                get_number = req_json['getNumber']

                if not order_id:
                    comfyui_loggerr.error("Invalid request: 'orderid' is required")
                    return error_response("'orderid' is required")
                if not dev_url:
                    comfyui_loggerr.error("Invalid request: 'devUrl' is required")
                    return error_response("'devUrl' is required")

                if not get_number:
                    comfyui_loggerr.error("Invalid request: 'getNumber' is required")
                    return error_response("'getNumber' is required")
                if get_number > Config.IMG_GEN_MAX:
                    return error_response(f"'getNumber' is No greater than {Config.IMG_GEN_MAX}")

                # 判断url有效
                try:
                    ve_dev_url = f'{dev_url}'
                    dev_url_response = requests.get(ve_dev_url)
                    dev_url_response.raise_for_status()

                except Exception as e:
                    return error_response(f"invalid URL {dev_url}")

                obj = ComfyuiApi(Config.GEN_IMAGE, order_id, dev_url)

                urls = []  # [productName,maskName,backendName,mbackendName]
                # 获取minio的图片的路径
                product_minio_ob_url: str = req_json['data']['productName']  # 产品图
                if validators.url(product_minio_ob_url):
                    urls.append(product_minio_ob_url)
                    comfyui_loggerr.debug(f"Valid product image URL: {product_minio_ob_url}")
                else:
                    comfyui_loggerr.error(f"Invalid product image URL product_minio_ob_url")
                    return error_response(f"Invalid url address product_minio_ob_url")

                mask_minio_ob_url: str = req_json['data']['maskName']  # 产品图
                if validators.url(mask_minio_ob_url):
                    urls.append(mask_minio_ob_url)
                    comfyui_loggerr.debug(f"Valid mask image URL: {mask_minio_ob_url}")
                else:
                    urls.append('')


                # 如果传输了手动背景图，自动背景图可有可无，如果没有那自动背景必须有
                mbackend_minio_ob_url: str = req_json['data'].get('mbackendName', None) # 手动背景图
                if mbackend_minio_ob_url and validators.url(mbackend_minio_ob_url):
                    backend_minio_ob_url: str = req_json['data']['backendName']  # 背景参考图
                    # 检测是否是有效的url地址
                    if validators.url(backend_minio_ob_url):
                        # urls.append(backend_minio_ob_url)
                        urls.append('')
                        comfyui_loggerr.debug(f"Valid backend image URL: {backend_minio_ob_url}")
                    else:
                        urls.append('')
                    urls.append(mbackend_minio_ob_url)
                    comfyui_loggerr.debug(f"Valid maback image URL: {mbackend_minio_ob_url}")
                else:
                    backend_minio_ob_url: str = req_json['data']['backendName']  # 背景参考图
                    # 检测是否是有效的url地址
                    if validators.url(backend_minio_ob_url):
                        urls.append(backend_minio_ob_url)
                        comfyui_loggerr.debug(f"Valid backend image URL: {backend_minio_ob_url}")
                    else:
                        comfyui_loggerr.error(f"Invalid backend image URL backend_minio_ob_url")
                        return error_response(f"Invalid url backend_minio_ob_url")
                    urls.append('')

                comfyui_loggerr.debug(f"Image URLs  waiting to download: {urls}")

                # 从minio下载urls的照片，上传到comfyui,返回上传的照片的名称
                images_path = asyncio.run(obj.d_u_images(urls, Config.IMAGES_TMP))
                # 获取工作流json文件 替换信息
                

                print(images_path)
                # 自动还是不自动背景的逻辑 # [productName,maskName,backendName,mbackendName]
                if images_path[0] == '':
                    comfyui_loggerr.error(f'Picture {backend_minio_ob_url} processing failed')
                    return error_response(f'Picture {backend_minio_ob_url} processing failed')
                if mbackend_minio_ob_url:
                    if images_path[3] == '':
                        comfyui_loggerr.error(f'Picture {mbackend_minio_ob_url} processing failed')
                        return error_response(f'Picture {mbackend_minio_ob_url} processing failed')
                else:
                    if images_path[2] == '':
                        comfyui_loggerr.error(f'Picture {mbackend_minio_ob_url} processing failed')
                        return error_response(f'Picture {mbackend_minio_ob_url} processing failed')


                work_json = obj.genImagePrompt(get_number,images_path[0],images_path[1],images_path[2],images_path[3])
                comfyui_loggerr.debug("Creating workflow with provided parameters")

                if not isinstance(work_json, dict):
                    comfyui_loggerr.error("Prompt must be a dictionary.")
                    return error_response("Prompt must be a dictionary.")

                # 创建Comfyui任务
                obj.create_work(work_json)

                comfyui_loggerr.debug("GEN_IMAGE create work successfully")
                return success_response(data='', message='')

            case Config.GEN_MANEQUIN:
                comfyui_loggerr.info("Processing GEN_MANEQUIN logic")
                # 实现 GEN_MANEQUIN 的逻辑处理
                order_id = req_json['orderid']
                dev_url = req_json.get('devUrl')
                desc = req_json['data']['desc']

                if not order_id:
                    comfyui_loggerr.error("Invalid request: 'orderid' is required")
                    return error_response("'orderid' is required")
                if not dev_url:
                    comfyui_loggerr.error("Invalid request: 'devUrl' is required")
                    return error_response("'devUrl' is required")

                    # 判断url有效
                try:
                    ve_dev_url = f'{dev_url}'
                    dev_url_response = requests.get(ve_dev_url)
                    dev_url_response.raise_for_status()

                except Exception as e:
                    return error_response(f"invalid URL {dev_url}")

                if not desc:
                    comfyui_loggerr.error("Invalid request: 'desc' is required")
                    return error_response("'desc' is required")

                obj = ComfyuiApi(Config.GEN_MANEQUIN, order_id, dev_url)

                urls = [] # [producName, maskName]
                # 获取minio的图片的路径
                product_minio_ob_url: str = req_json['data']['productName']  # 产品图
                if validators.url(product_minio_ob_url):
                    urls.append(product_minio_ob_url)
                    comfyui_loggerr.debug(f"Valid product image URL: {product_minio_ob_url}")
                else:
                    comfyui_loggerr.error(f"Invalid product image URL product_minio_ob_url")
                    return error_response(f"Invalid url address product_minio_ob_url")

                mask_minio_ob_url: str = req_json['data']['maskName']  # 产品图
                if validators.url(mask_minio_ob_url):
                    urls.append(mask_minio_ob_url)
                    comfyui_loggerr.debug(f"Valid mask image URL: {mask_minio_ob_url}")
                else:
                    comfyui_loggerr.error(f"Invalid product image URL mask_minio_ob_url")
                    return error_response(f"Invalid url address mask_minio_ob_url")


                comfyui_loggerr.debug(f"Image URLs  waiting to download: {urls}")
                images_path = asyncio.run(obj.d_u_images(urls, Config.IMAGES_TMP))
                # 获取工作流json文件 替换信息

                print(images_path)

                work_json = obj.genModChgPrompt(images_path[0],images_path[1], desc)
                comfyui_loggerr.debug(f"Creating workflow with provided parameters {work_json}")

                if not isinstance(work_json, dict):
                    comfyui_loggerr.error("Prompt must be a dictionary.")
                    return error_response("Prompt must be a dictionary.")

                # 创建Comfyui任务
                obj.create_work(work_json)

                comfyui_loggerr.debug("GEN_MANEQUIN create work successfully")

                return success_response(data='', message='')


            # 处理图片修复
            case Config.GEN_PICRST:
                comfyui_loggerr.info("Processing GEN_PICRST logic")
                order_id = req_json['orderid']
                dev_url = req_json.get('devUrl')

                if not order_id:
                    comfyui_loggerr.error("Invalid request: 'orderid' is required")
                    return error_response("'orderid' is required")
                if not dev_url:
                    comfyui_loggerr.error("Invalid request: 'devUrl' is required")
                    return error_response("'devUrl' is required")

                    # 判断url有效
                try:
                    ve_dev_url = f'{dev_url}'
                    dev_url_response = requests.get(ve_dev_url)
                    dev_url_response.raise_for_status()

                except Exception as e:
                    return error_response(f"invalid URL {dev_url}")

                obj = ComfyuiApi(Config.GEN_PICRST, order_id, dev_url)
                urls = []
                # 获取minio的图片的路径
                product_minio_ob_url: str = req_json['data']['productName']  # 产品图
                if validators.url(product_minio_ob_url):
                    urls.append(product_minio_ob_url)
                    comfyui_loggerr.debug(f"Valid product image URL: {product_minio_ob_url}")
                else:
                    comfyui_loggerr.error(f"Invalid product image URL product_minio_ob_url")
                    return error_response(f"Invalid url address product_minio_ob_url")

                comfyui_loggerr.debug(f"Image URLs  waiting to download: {urls}")
                images_path = asyncio.run(obj.d_u_images(urls, Config.IMAGES_TMP))

                print(images_path)

                work_json = obj.genPicRstPrompt(images_path[0])
                comfyui_loggerr.debug(f"Creating workflow with provided parameters {work_json}")

                # print(work_json)
                if not isinstance(work_json, dict):
                    comfyui_loggerr.error("Prompt must be a dictionary.")
                    return error_response("Prompt must be a dictionary.")

                # 创建Comfyui任务
                obj.create_work(work_json)

                comfyui_loggerr.debug("gen_image create work successfully")

                return success_response(data='', message='')


            # 处理抠图
            case Config.GEN_MATTING:
                comfyui_loggerr.info("Processing GEN_MATTING logic")
                order_id = req_json['orderid']
                dev_url = req_json.get('devUrl')

                if not order_id:
                    comfyui_loggerr.error("Invalid request: 'orderid' is required")
                    return error_response("'orderid' is required")
                if not dev_url:
                    comfyui_loggerr.error("Invalid request: 'devUrl' is required")
                    return error_response("'devUrl' is required")

                    # 判断url有效
                try:
                    ve_dev_url = f'{dev_url}'
                    dev_url_response = requests.get(ve_dev_url)
                    dev_url_response.raise_for_status()

                except Exception as e:
                    return error_response(f"invalid URL {dev_url}")

                obj = ComfyuiApi(Config.GEN_MATTING,order_id, dev_url)

                urls = []
                # 获取minio的图片的路径
                product_minio_ob_url: str = req_json['data']['productName']  # 产品图
                if validators.url(product_minio_ob_url):
                    urls.append(product_minio_ob_url)
                    comfyui_loggerr.debug(f"Valid product image URL: {product_minio_ob_url}")
                else:
                    comfyui_loggerr.error(f"Invalid product image URL product_minio_ob_url")
                    return error_response(f"Invalid url address product_minio_ob_url")

                comfyui_loggerr.debug(f"Image URLs  waiting to download: {urls}")
                images_path = asyncio.run(obj.d_u_images(urls, Config.IMAGES_TMP))
                # 获取工作流json文件 替换信息

                print(images_path)

                work_json = obj.genMattingPrompt(images_path[0])
                comfyui_loggerr.debug(f"Creating workflow with provided parameters {work_json}")

                if not isinstance(work_json, dict):
                    comfyui_loggerr.error("Prompt must be a dictionary.")
                    return error_response("Prompt must be a dictionary.")

                # 创建Comfyui任务
                obj.create_work(work_json)

                comfyui_loggerr.debug("GEN_MATTING create work successfully")

                return success_response(data='', message='')

            case Config.GEN_EXPIC:
                comfyui_loggerr.info("Processing GEN_EXPIC logic")
                order_id = req_json['orderid']
                dev_url = req_json.get('devUrl')
                desc = req_json['data']['desc']

                if not order_id:
                    comfyui_loggerr.error("Invalid request: 'orderid' is required")
                    return error_response("'orderid' is required")
                if not dev_url:
                    comfyui_loggerr.error("Invalid request: 'devUrl' is required")
                    return error_response("'devUrl' is required")

                    # 判断url有效
                try:
                    ve_dev_url = f'{dev_url}'
                    dev_url_response = requests.get(ve_dev_url)
                    dev_url_response.raise_for_status()

                except Exception as e:
                    return error_response(f"invalid URL {dev_url}")

                if not desc:
                    comfyui_loggerr.error("Invalid request: 'desc' is required")
                    return error_response("'desc' is required")

                obj = ComfyuiApi(Config.GEN_EXPIC, order_id, dev_url)

                urls = []
                # 获取minio的图片的路径
                product_minio_ob_url: str = req_json['data']['productName']  # 产品图
                if validators.url(product_minio_ob_url):
                    urls.append(product_minio_ob_url)
                    comfyui_loggerr.debug(f"Valid product image URL: {product_minio_ob_url}")
                else:
                    comfyui_loggerr.error(f"Invalid product image URL product_minio_ob_url")
                    return error_response(f"Invalid url address product_minio_ob_url")

                comfyui_loggerr.debug(f"Image URLs  waiting to download: {urls}")
                images_path = asyncio.run(obj.d_u_images(urls, Config.IMAGES_TMP))
                # 获取工作流json文件 替换信息

                print(images_path)

                work_json = obj.genPicExpPrompt(images_path[0], desc)
                comfyui_loggerr.debug(f"Creating workflow with provided parameters {work_json}")

                if not isinstance(work_json, dict):
                    comfyui_loggerr.error("Prompt must be a dictionary.")
                    return error_response("Prompt must be a dictionary.")

                # 创建Comfyui任务
                obj.create_work(work_json)

                comfyui_loggerr.debug("GEN_MATTING create work successfully")

                return success_response(data='', message='')
            case _:
                comfyui_loggerr.error(f"Unknown workerType value: {get_type}")
                return error_response(f"Unknown workerType: {get_type}")

    except KeyError as e:
        comfyui_loggerr.error(f"KeyError - Missing key in request data: {str(e)}")
        return error_response(f"Missing key: {str(e)}")

    except Exception as e:
        comfyui_loggerr.error(f"Unexpected error in gen_image: {str(e)}")
        return error_response(f"An unexpected error occurred: {e}")


@comfyui_bp.route('/api/outer/ginfo', methods=['GET'])
def get_info():

    try:
        # 从查询字符串获取普通参数
        devUrl = request.args.get('devUrl')
        type = request.args.get('type')
        comfyui_loggerr.debug(f"Request data received: {devUrl, type}")

        match type:
            case 'queue':
                # https://u285042-8989-83157279.bjb1.seetacloud.com:8443/prompt
                try:
                    url = f"https://{devUrl}/prompt"
                    # 发送POST请求
                    response = requests.get(url)
                    response.raise_for_status()  # 确保请求成功
                    data = {
                        "queue_remaining":response.json()['exec_info']['queue_remaining']
                    }
                    comfyui_loggerr.debug(f"")
                    return success_response(data=data, message='')

                except requests.exceptions.RequestException as e:
                    comfyui_loggerr.error(f"Error request for {e} ")
                    return error_response(f"Not Found for url: {devUrl}")

            case _:
                comfyui_loggerr.error(f"Unknown Type value: {type}")
                return error_response(f"Unknown Type: {type}")



    except KeyError as e:
        comfyui_loggerr.error(f"KeyError - Missing key in request data: {str(e)}")
        return error_response(f"Missing key: {str(e)}")

    except Exception as e:
        comfyui_loggerr.error(f"Unexpected error in gen_image: {str(e)}")
        return error_response(f"An unexpected error occurred: {e}")


@comfyui_bp.route('/api/outer/pinfo', methods=['POST'])
def post_info():

    try:
        # 获取请求数据并转为 JSON 格式
        req_json = request.get_json()
        if req_json is None:
            comfyui_loggerr.error("Invalid request: No JSON data found")
            return error_response("No JSON data found")

        comfyui_loggerr.debug(f"Request data received: {req_json}")




    except KeyError as e:
        comfyui_loggerr.error(f"KeyError - Missing key in request data: {str(e)}")
        return error_response(f"Missing key: {str(e)}")

    except Exception as e:
        comfyui_loggerr.error(f"Unexpected error in gen_image: {str(e)}")
        return error_response(f"An unexpected error occurred: {e}")