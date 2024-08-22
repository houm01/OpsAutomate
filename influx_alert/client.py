

from .endpoints.network import NetworkEndpoint
from .endpoints.vmware import VMWareEndpoint
from .endpoints.common import CommonEndpoint
from .endpoints.extensions import ExtensionsEndpoint
from influxdb import InfluxDBClient
import urllib3
urllib3.disable_warnings()
from pymongo import MongoClient

#test


class BaseClient:
    
    def __init__(self, 
                 influx_host: str=None,
                 influx_port: int=8086,
                 influx_username: str=None,
                 influx_password: str=None,
                 influx_database: str='telegraf',
                 influx_ssl: bool=True,
                 mongo_host: str='127.0.0.1',
                 mongo_port: int=27017,
                 mongo_username: str=None,
                 mongo_password: str=None,
                 mongo_authsource: str='admin',
                 mongo_database: str='automate',
                 feishu_app_id: str=None,
                 feishu_app_secret: str=None,
                 feishu_card_template_id: str=None,
                 feishu_card_receive_id: str=None,
                 wecom_webhook_url: str=None,
                 onealert_webhook_url: str=None,
                 debug: bool=False):
        
        self._influx_host = influx_host
        self._influx_port = influx_port
        self._influx_username = influx_username
        self._influx_password = influx_password
        self._influx_database = influx_database
        self._influx_ssl = influx_ssl

        self._mongo_host = mongo_host
        self._mongo_port = mongo_port
        self._mongo_username = mongo_username
        self._mongo_password = mongo_password
        self._mongo_authsource = mongo_authsource
        self._mongo_database = mongo_database


        self.feishu_app_id = feishu_app_id
        self.feishu_app_secret = feishu_app_secret
        self.feishu_card_template_id = feishu_card_template_id
        # self.feishu_card_template_variable = feishu_card_template_variable
        self.feishu_card_receive_id = feishu_card_receive_id
        
        self.wecom_webhook_url = wecom_webhook_url
        self.onealert_webhook_url = onealert_webhook_url
        
        self.debug = debug
        
        self.influx_client = self._build_influxdb_client()
        self.mongo_client = self._build_mongo_client()
        self.feishu_client = self._build_feishu_client()

        self.network = NetworkEndpoint(self)
        self.vmware = VMWareEndpoint(self)
        self.extensions = ExtensionsEndpoint(self)
        self.common = CommonEndpoint(self)
        

    def _build_influxdb_client(self):
        pass

    def _build_mongo_client(self):
        pass
    
    def _build_feishu_client(self):
        pass

class Client(BaseClient):
    def _build_influxdb_client(self):
        return InfluxDBClient(host=self._influx_host, 
                        port=self._influx_port,
                        username=self._influx_username,
                        password=self._influx_password,
                        database=self._influx_database,
                        ssl=self._influx_ssl)
        
    def _build_mongo_client(self):
        client = MongoClient(host=self._mongo_host,
                             port=self._mongo_port,
                             username=self._mongo_username,
                             password=self._mongo_password,
                             authSource=self._mongo_authsource)
        if self.debug:
            return client[self._mongo_database]['alert_debug'] 
        else:
            print(self._mongo_database)
            return client[self._mongo_database]['alert']
    
    def _build_feishu_client(self):
        if self.feishu_app_id:
            from cc_feishu.client import Client as FeishuClient
            return FeishuClient(app_id=self.feishu_app_id, app_secret=self.feishu_app_secret)
    