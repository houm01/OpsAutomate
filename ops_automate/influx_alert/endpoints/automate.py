#!/usr/bin/env python3


import datetime

import yagmail

from openpyxl import Workbook

from ..endpoint import Endpoint
from nb_log import get_logger



log = get_logger('automate')

class AutomateEndpoint(Endpoint):
    
    def export_alert_to_excel(self, 
                              sender_mail_username,
                              sender_mail_password,
                              sender_mail_smtp_address,
                              received_mail):
        
        wb_name = str(datetime.date.today()) + '_' + '告警列表'
        
        results = self.parent.mongo_client.find(
            {},
            {"_id": 0, "restore_influx": 0}
        )
        wb = Workbook()
        ws = wb.create_sheet('alert', 0)
        
        
        for result in results:
            # print()
            ws.append(list(result.keys()))
            break
        for result in results:
            # ws.append(['主机名', 'SN', 'U位', '厂家', '机房', '机柜', '状态', '设备类型'])
            ws.append(list(result.values()))
            
            wb.save(f'{wb_name}.xlsx')
            wb.close()
              
        yag = yagmail.SMTP(user=sender_mail_username, password=sender_mail_password, host=sender_mail_smtp_address)
        contents = f'{wb_name}'
        yag.send(to=received_mail, subject=f'{wb_name}', contents=contents, attachments=[f'{wb_name}.xlsx'])
        yag.close()
        return results

