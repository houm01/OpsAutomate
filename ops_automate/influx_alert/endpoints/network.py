from ..endpoint import Endpoint
from nb_log import get_logger

log = get_logger('network')


ALARM_NAME_TRAFFIC = '流量超出设置的阀值'
ALARM_NAME_PORT_DOWN = '端口DOWN'

class NetworkEndpoint(Endpoint):
    
    def ping_unreachable(self, limit: int=3):
        QUERY = f"""select
            "percent_packet_loss", 
            "name", 
            "url", 
            "result_code" 
            from ping 
            where time > now() - 1d 
            group by "url" 
            order by desc 
            limit {limit}"""
        
        log.debug(QUERY)
        
        for results in self.parent.influx_client.query(QUERY):
            has_loss = all(result['percent_packet_loss'] == 100.0 for result in results)
            if has_loss:
                r = results[0]
                url = r['url']
                alarm_content = '{} Ping不可达'.format(r['name'])
                log.info(f'发现告警: [{alarm_content}]')
                self.parent.extensions.tool_check_insert_send_mongo(
                    restore_influx=f"""select "percent_packet_loss" from ping where "url" = '{url}' order by time desc limit {limit}""",
                    url=url,
                    alarm_name='Ping 不可达',
                    entity_name=url,
                    alarm_content=alarm_content,
                    alarm_time=self.parent.extensions.time_get_now_time_mongo(),
                    priority='High',
                    is_notify=True)

        for mongo_item in self.parent.extensions.mongo_query_trigger(alarm_name='Ping 不可达'):
            for results in self.parent.influx_client.query(mongo_item['restore_influx']):
                # print(i)
                all_zero = all(result['percent_packet_loss'] == 0.0 for result in results)
                if all_zero:
                    self.parent.extensions.tool_check_insert_send_mongo(
                        event_type='resolved',
                        mongo_id=mongo_item['_id'],
                        event_id=mongo_item['event_id'],
                        entity_name=mongo_item['entity_name'],
                        alarm_name=mongo_item['alarm_name'],
                        alarm_content=mongo_item['alarm_content'],
                        priority=mongo_item['priority'],
                        is_notify=True)

    def packet_loss(self, name: str=None, last_minute: int=10, packet_loss_percent_trigger: int=0.05):
        
        QUERY = f"""select "{name}", "percent_packet_loss", "url" from ping WHERE time > now() - {last_minute}m group by url"""
            
        log.debug(f'packet loss trigger, 查询语法: [{QUERY}]')
        
        for results in self.parent.influx_client.query(QUERY):        
            count_packet_loss = 0
            for result in results:
                if result['percent_packet_loss'] != 0.0:
                    count_packet_loss += 1
            
            packet_loss_percent = count_packet_loss / len(results)
            
            # log.info(packet_loss_percent)
            if 1.0 > packet_loss_percent > packet_loss_percent_trigger:
                
                try:
                    name = results[0][name]
                except KeyError:
                    log.error(f'获取name失败, results为 {results[0]}')
                    name = 'null'
                url = results[0]['url']
                
                alarm_content = f'{name} {url} Ping 丢包率超阀值'
                self.parent.extensions.tool_check_insert_send_mongo(
                    restore_influx=f"""select "percent_packet_loss" from ping where "url" = '{url}' and time > now() - {last_minute}m""",
                    url=url,
                    alarm_name='Ping 丢包率超阀值',
                    entity_name=url,
                    alarm_content=alarm_content,
                    alarm_time=self.parent.extensions.time_get_now_time_mongo(),
                    priority='Warning',
                    is_notify=True,
                    automate_ts=f'设定的阀值为{packet_loss_percent_trigger* 100:.0f}%, 近{last_minute}分钟丢包率为{packet_loss_percent * 100:.0f}%')
                
        for mongo_item in self.parent.extensions.mongo_query_trigger(alarm_name='Ping 丢包率超阀值'):
            for results in self.parent.influx_client.query(mongo_item['restore_influx']):
                
                count_packet_loss = 0
                for result in results:
                    if result['percent_packet_loss'] == 0.0:
                        count_packet_loss += 1
                        
                packet_loss_percent = count_packet_loss / len(results)
                if packet_loss_percent > packet_loss_percent_trigger:
                    self.parent.extensions.tool_check_insert_send_mongo(
                        event_type='resolved',
                        mongo_id=mongo_item['_id'],
                        event_id=mongo_item['event_id'],
                        entity_name=mongo_item['entity_name'],
                        alarm_name=mongo_item['alarm_name'],
                        alarm_content=mongo_item['alarm_content'],
                        priority=mongo_item['priority'],
                        is_notify=True)

    def port_traffic(self, 
             sysname: str=None, 
             agent_host: str=None, 
             ifname: str=None, 
             last_minute: int=30,
             direction: str='inbound',
             threshold: int=100,
             remark: str=''):
        
        if sysname:
            query_property = 'sysName'
            query_value = sysname
            
        
        if agent_host:
            query_property = 'agent_host'
            query_value = agent_host
        
        if direction == 'inbound':
            direction = 'ifHCInOctets'
        elif direction == 'outbound':
            direction = 'ifHCOutOctets'
        
        query = f"""
    select mean(rate) 
    from 
    (SELECT derivative(mean("{direction}"), 1s) * 8 / 1000000 as "rate"
    FROM "interface" WHERE ("{query_property}" = '{query_value}') 
    AND ("ifName" = '{ifname}') 
    AND time > now() - {last_minute}m 
    GROUP BY time(1s), "ifName" fill(null))
    """
    
        log.debug(f'query: [{query.strip()}]')
        for results in self.parent.influx_client.query(query=query):
            # diff_now = self.parent.extensions.time_diff_influx_now(source_time=results['time'])
            log.debug(results)
            traffic_speed = int(results[0]['mean'])
            
            if traffic_speed > threshold:
                
                restore_influx = query.replace('as ', f' - {threshold} as ') + '分隔线' + query
                log.info(f'restore_influx: [{restore_influx}]')
                self.parent.extensions.tool_check_insert_send_mongo(
                    restore_influx=restore_influx,
                    alarm_content= f'{remark}{ALARM_NAME_TRAFFIC},阀值为{threshold}Mbit/s',
                    alarm_name=ALARM_NAME_TRAFFIC,
                    priority='中',
                    entity_name=query_value,
                    alarm_time=self.parent.extensions.time_get_now_time_mongo(),
                    automate_ts=f'当前流量值为{traffic_speed}Mbit/s',
                    is_notify=True)

            
        for mongo_item in self.parent.extensions.mongo_query_trigger(alarm_name=ALARM_NAME_TRAFFIC):
            log.debug('恢复语法: ' + mongo_item['restore_influx'])
            
            all_query = mongo_item['restore_influx'].replace('\\n', '')
            query, current_traffic = all_query.split('分隔线')[0], all_query.split('分隔线')[1]
            log.debug(query)
            for results in self.parent.influx_client.query(query):
                
                log.debug(results)
                
                if results[0]['mean'] < 0:
                    self.parent.extensions.tool_check_insert_send_mongo(
                        mongo_id = mongo_item['_id'],
                        event_type='resolved',
                        alarm_content= mongo_item['alarm_content'],
                        alarm_name=ALARM_NAME_TRAFFIC,
                        priority=mongo_item['priority'],
                        alarm_time=self.parent.extensions.time_get_now_time_mongo(),
                        entity_name=mongo_item['entity_name'],
                        automate_ts=f'当前流量值为{traffic_speed}Mbit/s',
                        is_notify=True)
    
    def port_down(self, 
                sysname: str=None, 
                agent_host: str=None, 
                ifdescr: str=None, 
                remark: str=''):
        query = f"""
        select "sysName", last("ifOperStatus") as ifOperStatus, "ifDescr" 
from interface 
where "sysName" = '{sysname}' and "ifDescr" = '{ifdescr}' and time > now() - 1d"""

        for results in self.parent.influx_client.query(query=query):
            # log.debug(results)
            alarm_content = results[0]['sysName'] + ' ' + results[0]['ifDescr'] + ' 端口DOWN'
            
            if results[0]['ifOperStatus'] != 'up':
                self.parent.extensions.tool_check_insert_send_mongo(
                    restore_influx=f"""select "sysName", last("ifOperStatus") as ifOperStatus, "ifDescr" from interface where "sysName" = '{sysname}' and "ifDescr" = '{ifdescr}'""",
                    alarm_content= alarm_content,
                    alarm_name=ALARM_NAME_PORT_DOWN,
                    priority='中',
                    entity_name=results[0]['sysName'],
                    alarm_time=self.parent.extensions.time_get_now_time_mongo(),
                    automate_ts='',
                    is_notify=True)
                
        # 恢复告警
        for mongo_item in self.parent.extensions.mongo_query_trigger(alarm_name=ALARM_NAME_PORT_DOWN):
            log.debug('恢复语法: ' + mongo_item['restore_influx'])
            for results in self.parent.influx_client.query(mongo_item['restore_influx']):
                
                log.debug(results)
                if results[0]['ifOperStatus'] == 'up':
                    self.parent.extensions.tool_check_insert_send_mongo(
                        mongo_id = mongo_item['_id'],
                        event_type='resolved',
                        alarm_content= mongo_item['alarm_content'] + '已恢复',
                        alarm_name=ALARM_NAME_PORT_DOWN,
                        priority=mongo_item['priority'],
                        alarm_time=self.parent.extensions.time_get_now_time_mongo(),
                        entity_name=mongo_item['entity_name'],
                        automate_ts=f'',
                        is_notify=True)