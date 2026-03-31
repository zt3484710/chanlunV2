# -*- coding: utf-8 -*-
"""缠论结构算法 - 完整迁移自旧版 chanlun.py

包含：分型识别、笔识别、线段识别、中枢识别、背驰判断、买卖点信号、走势终结判断
"""
import pandas as pd
import numpy as np
from typing import List, Dict
from app.services.chanlun_analysis import calculate_macd


def process_kline_inclusion(df: pd.DataFrame) -> pd.DataFrame:
    """
    K线包含处理 - 简化版，暂时跳过包含处理
    保留原始K线数据用于分型识别
    """
    result = []
    for i in range(len(df)):
        row = df.iloc[i]
        result.append({
            'index': i,  # 保留原始索引
            'date': row['date'],
            'high': float(row['high']),
            'low': float(row['low']),
            'open': float(row['open']),
            'close': float(row['close'])
        })
    
    return pd.DataFrame(result)


def find_fenxing(df: pd.DataFrame) -> List[Dict]:
    """
    识别分型
    顶分型：中间K线高点最高
    底分型：中间K线低点最低
    """
    fenxing_list = []
    
    if len(df) < 3:
        return fenxing_list
    
    for i in range(1, len(df) - 1):
        prev = df.iloc[i - 1]
        curr = df.iloc[i]
        next_k = df.iloc[i + 1]
        
        # 顶分型：中间K线高点最高
        if curr['high'] > prev['high'] and curr['high'] > next_k['high']:
            fenxing_list.append({
                'index': int(curr['index']),
                'date': str(curr['date']),
                'type': 'top',
                'price': float(curr['high'])
            })
        
        # 底分型：中间K线低点最低
        elif curr['low'] < prev['low'] and curr['low'] < next_k['low']:
            fenxing_list.append({
                'index': int(curr['index']),
                'date': str(curr['date']),
                'type': 'bottom',
                'price': float(curr['low'])
            })
    
    return fenxing_list


def find_bi(fenxing_list: List[Dict]) -> List[Dict]:
    """
    识别笔
    相邻顶底分型之间构成一笔，中间至少有1根独立K线
    笔必须首尾相连，形成连续折线
    """
    if len(fenxing_list) < 2:
        return []
    
    bi_list = []
    
    # 从第一个分型开始，寻找有效的笔
    i = 0
    while i < len(fenxing_list) - 1:
        curr = fenxing_list[i]
        
        # 寻找下一个相反类型的分型
        j = i + 1
        while j < len(fenxing_list) and fenxing_list[j]['type'] == curr['type']:
            j += 1
        
        if j >= len(fenxing_list):
            break
        
        next_fx = fenxing_list[j]
        
        # 检查是否有足够的独立K线（至少1根）
        if next_fx['index'] - curr['index'] < 2:
            i += 1
            continue
        
        # 检查顶底关系
        if curr['type'] == 'top' and next_fx['type'] == 'bottom':
            # 顶到底，顶必须高于底
            if curr['price'] <= next_fx['price']:
                i += 1
                continue
            direction = 'down'
        elif curr['type'] == 'bottom' and next_fx['type'] == 'top':
            # 底到顶，底必须低于顶
            if curr['price'] >= next_fx['price']:
                i += 1
                continue
            direction = 'up'
        else:
            i += 1
            continue
        
        bi_list.append({
            'start_index': int(curr['index']),
            'start_date': str(curr['date']),
            'start_price': float(curr['price']),
            'end_index': int(next_fx['index']),
            'end_date': str(next_fx['date']),
            'end_price': float(next_fx['price']),
            'direction': direction
        })
        
        i = j  # 从当前笔的终点继续
    
    return bi_list


def find_xianduan(bi_list: List[Dict]) -> List[Dict]:
    """
    识别线段
    至少3笔构成线段，有方向性
    线段破坏：被反向线段破坏
    """
    if len(bi_list) < 3:
        return []
    
    xianduan_list = []
    
    # 从第一笔开始构建线段
    i = 0
    while i < len(bi_list) - 2:
        # 检查连续3笔是否形成线段
        bi1 = bi_list[i]
        bi2 = bi_list[i + 1]
        bi3 = bi_list[i + 2]
        
        # 线段方向由第一笔决定
        direction = bi1['direction']
        
        # 检查是否符合线段结构：同-反-同
        if bi1['direction'] == bi3['direction'] and bi2['direction'] != bi1['direction']:
            # 形成线段
            xianduan_list.append({
                'start_index': int(bi1['start_index']),
                'start_date': str(bi1['start_date']),
                'start_price': float(bi1['start_price']),
                'end_index': int(bi3['end_index']),
                'end_date': str(bi3['end_date']),
                'end_price': float(bi3['end_price']),
                'direction': direction,
                'bi_count': 3
            })
            i += 2  # 跳过已使用的笔
        else:
            i += 1
    
    return xianduan_list


def find_zhongshu(xianduan_list: List[Dict]) -> List[Dict]:
    """
    识别中枢
    三段次级别走势重叠部分
    """
    if len(xianduan_list) < 3:
        return []
    
    zhongshu_list = []
    
    for i in range(len(xianduan_list) - 2):
        xd1 = xianduan_list[i]
        xd2 = xianduan_list[i + 1]
        xd3 = xianduan_list[i + 2]
        
        # 计算高低点
        highs = [xd1['start_price'], xd1['end_price'], 
                 xd2['start_price'], xd2['end_price'],
                 xd3['start_price'], xd3['end_price']]
        lows = [xd1['start_price'], xd1['end_price'],
                xd2['start_price'], xd2['end_price'],
                xd3['start_price'], xd3['end_price']]
        
        zg = min(max(highs[:2]), max(highs[2:4]), max(highs[4:]))  # 中枢高点
        zd = max(min(lows[:2]), min(lows[2:4]), min(lows[4:]))     # 中枢低点
        
        if zg > zd:  # 有重叠
            zhongshu_list.append({
                'start_index': int(xd1['start_index']),
                'end_index': int(xd3['end_index']),
                'zg': float(zg),
                'zd': float(zd),
                'center': float((zg + zd) / 2)
            })
    
    return zhongshu_list


def check_divergence(bi_list: List[Dict], macd_data: Dict) -> List[Dict]:
    """
    判断笔是否背驰
    参数:
        bi_list: 笔列表
        macd_data: MACD数据 (dif, dea, hist)
    返回:
        背驰信息列表
    """
    divergence_list = []
    
    if len(bi_list) < 2:
        return divergence_list
    
    # 提取MACD数据
    dif = macd_data.get('dif', [])
    dea = macd_data.get('dea', [])
    hist = macd_data.get('hist', [])
    
    # 遍历笔，比较连续的同向笔
    for i in range(len(bi_list) - 1):
        bi1 = bi_list[i]
        bi2 = bi_list[i + 1]
        
        # 只比较同向的笔（上-上 或 下-下）
        if bi1['direction'] != bi2['direction']:
            continue
        
        # 确定笔的范围对应的MACD数据
        start_idx1 = bi1['start_index']
        end_idx1 = bi1['end_index']
        start_idx2 = bi2['start_index']
        end_idx2 = bi2['end_index']
        
        # 确保索引在MACD数据范围内
        if (end_idx1 >= len(hist) or end_idx2 >= len(hist) or
            start_idx1 < 0 or start_idx2 < 0):
            continue
        
        # 计算两段的MACD面积（绝对值之和）
        area1 = sum(abs(h) for h in hist[start_idx1:end_idx1+1])
        area2 = sum(abs(h) for h in hist[start_idx2:end_idx2+1])
        
        # 获取两段的价格极值和MACD极值
        if bi1['direction'] == 'up':
            # 上涨笔：比较高点
            price1 = bi1['end_price']
            price2 = bi2['end_price']
            
            # 比较DIF高度
            dif1 = max(dif[start_idx1:end_idx1+1])
            dif2 = max(dif[start_idx2:end_idx2+1])
            
            # 判断顶背驰：价格创新高，MACD不创新高，面积缩小
            if price2 > price1 and dif2 <= dif1 and area2 < area1:
                # 计算背驰强度
                strength = 1.0 - (area2 / area1) if area1 > 0 else 0
                divergence_list.append({
                    'position': end_idx2,
                    'bi_index': i + 1,
                    'type': 'top',
                    'strength': float(strength),
                    'price': float(price2),
                    'date': bi2['end_date']
                })
        else:
            # 下跌笔：比较低点
            price1 = bi1['end_price']
            price2 = bi2['end_price']
            
            # 比较DIF高度（绝对值）
            dif1 = min(dif[start_idx1:end_idx1+1])
            dif2 = min(dif[start_idx2:end_idx2+1])
            
            # 判断底背驰：价格创新低，MACD不创新低，面积缩小
            if price2 < price1 and dif2 >= dif1 and area2 < area1:
                # 计算背驰强度
                strength = 1.0 - (area2 / area1) if area1 > 0 else 0
                divergence_list.append({
                    'position': end_idx2,
                    'bi_index': i + 1,
                    'type': 'bottom',
                    'strength': float(strength),
                    'price': float(price2),
                    'date': bi2['end_date']
                })
    
    return divergence_list


def find_buy_sell_signals(bi_list, xianduan_list, zhongshu_list, fenxing_list, prices, divergence_list=None):
    """
    识别买卖点信号
    参数:
        bi_list: 笔列表
        xianduan_list: 线段列表
        zhongshu_list: 中枢列表
        fenxing_list: 分型列表
        prices: 价格数据 (DataFrame)
        divergence_list: 背驰列表 (可选)
    返回:
        信号列表，每个信号包含: type, position, price, date
    """
    signals = []
    
    if not bi_list or len(bi_list) < 2:
        return signals
    
    # 如果没有提供背驰列表，先从价格数据计算
    if divergence_list is None:
        df_with_macd = calculate_macd(prices)
        macd_data = {
            'dif': df_with_macd['dif'].tolist() if 'dif' in df_with_macd.columns else [],
            'dea': df_with_macd['dea'].tolist() if 'dea' in df_with_macd.columns else [],
            'hist': df_with_macd['macd'].tolist() if 'macd' in df_with_macd.columns else []
        }
        divergence_list = check_divergence(bi_list, macd_data)
    
    # 创建背驰位置索引，方便查找
    divergence_positions = {d['position']: d for d in divergence_list}
    
    # 1. 识别一买和一卖（基于背驰）
    for div in divergence_list:
        if div['type'] == 'bottom':
            # 底背驰 -> 一买
            signals.append({
                'type': 'buy1',
                'position': div['position'],
                'price': div['price'],
                'date': div['date']
            })
        elif div['type'] == 'top':
            # 顶背驰 -> 一卖
            signals.append({
                'type': 'sell1',
                'position': div['position'],
                'price': div['price'],
                'date': div['date']
            })
    
    # 2. 识别二买和二卖（基于笔结构）
    for i in range(2, len(bi_list)):
        bi1 = bi_list[i-2]
        bi2 = bi_list[i-1]
        bi3 = bi_list[i]
        
        # 二买：上涨后第一次回调不破前低
        # 结构：上-下-上，且回调低点不破前低
        if (bi1['direction'] == 'up' and bi2['direction'] == 'down' and bi3['direction'] == 'up'):
            if bi2['end_price'] > bi1['start_price']:  # 回调不破前低
                signals.append({
                    'type': 'buy2',
                    'position': bi3['start_index'],
                    'price': bi3['start_price'],
                    'date': bi3['start_date']
                })
        
        # 二卖：下跌后第一次反弹不过前高
        # 结构：下-上-下，且反弹高点不过前高
        if (bi1['direction'] == 'down' and bi2['direction'] == 'up' and bi3['direction'] == 'down'):
            if bi2['end_price'] < bi1['start_price']:  # 反弹不过前高
                signals.append({
                    'type': 'sell2',
                    'position': bi3['start_index'],
                    'price': bi3['start_price'],
                    'date': bi3['start_date']
                })
    
    # 3. 识别三买和三卖（基于中枢突破）
    for zhongshu in zhongshu_list:
        zg = zhongshu['zg']  # 中枢高点
        zd = zhongshu['zd']  # 中枢低点
        
        # 查找中枢结束后的笔
        for i, bi in enumerate(bi_list):
            if bi['start_index'] > zhongshu['end_index']:
                # 三买：突破中枢高点后回踩不破
                if bi['direction'] == 'up' and bi['end_price'] > zg:
                    # 查找回踩笔
                    for j in range(i+1, len(bi_list)):
                        callback_bi = bi_list[j]
                        if callback_bi['direction'] == 'down' and callback_bi['end_price'] >= zg:
                            signals.append({
                                'type': 'buy3',
                                'position': callback_bi['end_index'],
                                'price': callback_bi['end_price'],
                                'date': callback_bi['end_date']
                            })
                            break
                
                # 三卖：跌破中枢低点后反弹不过
                if bi['direction'] == 'down' and bi['end_price'] < zd:
                    # 查找反弹笔
                    for j in range(i+1, len(bi_list)):
                        rebound_bi = bi_list[j]
                        if rebound_bi['direction'] == 'up' and rebound_bi['end_price'] <= zd:
                            signals.append({
                                'type': 'sell3',
                                'position': rebound_bi['end_index'],
                                'price': rebound_bi['end_price'],
                                'date': rebound_bi['end_date']
                            })
                            break
                break
    
    # 按位置排序信号
    signals.sort(key=lambda x: x['position'])
    
    return signals


def check_trend_completion(bi_list, xianduan_list, zhongshu_list, current_price):
    """
    判断走势是否终结
    参数:
        bi_list: 笔列表
        xianduan_list: 线段列表
        zhongshu_list: 中枢列表
        current_price: 当前价格
    返回:
        终结信息，包含：
        - completed: 是否终结
        - type: 终结类型 ('consolidation_breakout' 盘整终结, 'trend_divergence' 趋势终结, None 未终结)
        - position: 终结位置
        - price: 终结价格
        - direction: 终结方向 ('up' 向上终结, 'down' 向下终结)
    """
    result = {
        'completed': False,
        'type': None,
        'position': None,
        'price': None,
        'direction': None
    }
    
    # 如果数据不足，直接返回
    if not bi_list or len(bi_list) < 2:
        return result
    
    # === 1. 判断盘整终结 ===
    if zhongshu_list:
        # 获取最后一个中枢
        last_zhongshu = zhongshu_list[-1]
        zg = last_zhongshu['zg']  # 中枢高点
        zd = last_zhongshu['zd']  # 中枢低点
        
        # 检查是否突破中枢区间
        if current_price > zg:
            # 向上突破中枢 - 盘整终结
            result['completed'] = True
            result['type'] = 'consolidation_breakout'
            result['position'] = last_zhongshu['end_index']
            result['price'] = current_price
            result['direction'] = 'up'
            return result
        elif current_price < zd:
            # 向下跌破中枢 - 盘整终结
            result['completed'] = True
            result['type'] = 'consolidation_breakout'
            result['position'] = last_zhongshu['end_index']
            result['price'] = current_price
            result['direction'] = 'down'
            return result
    
    # === 2. 判断趋势终结 ===
    if xianduan_list and len(xianduan_list) >= 2:
        # 获取最后两个线段
        last_xd = xianduan_list[-1]
        prev_xd = xianduan_list[-2]
        
        # 判断是否有连续的反向线段
        if last_xd['direction'] != prev_xd['direction']:
            # 检查最后几笔是否有反向破坏
            if len(bi_list) >= 3:
                last_bi = bi_list[-1]
                prev_bi = bi_list[-2]
                
                # 连续出现反向笔
                if last_bi['direction'] != prev_bi['direction']:
                    # 趋势终结判断
                    result['completed'] = True
                    result['type'] = 'trend_divergence'
                    result['position'] = last_bi['end_index']
                    result['price'] = last_bi['end_price']
                    result['direction'] = last_bi['direction']
                    return result
    
    # === 3. 简单的笔破坏判断（备用） ===
    if len(bi_list) >= 3:
        # 检查最后三笔是否形成反向破坏
        bi1 = bi_list[-3]
        bi2 = bi_list[-2]
        bi3 = bi_list[-1]
        
        # 同-反-同结构，反向破坏
        if bi1['direction'] == bi3['direction'] and bi2['direction'] != bi1['direction']:
            # 检查是否突破前高/前低
            if bi1['direction'] == 'up' and bi3['end_price'] < bi1['start_price']:
                # 上涨趋势被反向破坏
                result['completed'] = True
                result['type'] = 'trend_divergence'
                result['position'] = bi3['end_index']
                result['price'] = bi3['end_price']
                result['direction'] = 'down'
                return result
            elif bi1['direction'] == 'down' and bi3['end_price'] > bi1['start_price']:
                # 下跌趋势被反向破坏
                result['completed'] = True
                result['type'] = 'trend_divergence'
                result['position'] = bi3['end_index']
                result['price'] = bi3['end_price']
                result['direction'] = 'up'
                return result
    
    return result


def analyze_chanlun(df: pd.DataFrame) -> Dict:
    """
    完整的缠论分析流程
    """
    # 1. K线包含处理
    df_processed = process_kline_inclusion(df)
    
    # 2. 识别分型
    fenxing_list = find_fenxing(df_processed)
    
    # 3. 识别笔
    bi_list = find_bi(fenxing_list)
    
    # 4. 识别线段
    xianduan_list = find_xianduan(bi_list)
    
    # 5. 识别中枢
    zhongshu_list = find_zhongshu(xianduan_list)
    
    # 6. 计算MACD数据（用于背驰判断）
    df_with_macd = calculate_macd(df)
    macd_data = {
        'dif': df_with_macd['dif'].tolist() if 'dif' in df_with_macd.columns else [],
        'dea': df_with_macd['dea'].tolist() if 'dea' in df_with_macd.columns else [],
        'hist': df_with_macd['macd'].tolist() if 'macd' in df_with_macd.columns else []
    }
    
    # 7. 背驰判断
    divergence_list = check_divergence(bi_list, macd_data)
    
    # 8. 买卖点信号识别
    signals = find_buy_sell_signals(bi_list, xianduan_list, zhongshu_list, fenxing_list, df, divergence_list)
    
    # 9. 走势终完美判断
    current_price = float(df.iloc[-1]['close']) if len(df) > 0 else 0.0
    trend_completion = check_trend_completion(bi_list, xianduan_list, zhongshu_list, current_price)
    
    return {
        'fenxing_list': fenxing_list,
        'bi_list': bi_list,
        'xianduan_list': xianduan_list,
        'zhongshu_list': zhongshu_list,
        'divergence_list': divergence_list,
        'signals': signals,
        'trend_completion': trend_completion
    }
