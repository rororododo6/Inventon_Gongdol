#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON 통신 디버깅 및 검증 도구
Arduino와의 통신 문제 진단 및 해결을 위한 유틸리티
"""

import json
import time
import serial
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import argparse

def validate_json_message(message: str) -> Dict[str, Any]:
    """
    JSON 메시지 유효성 검증
    
    Args:
        message: JSON 문자열
        
    Returns:
        검증 결과
    """
    result = {
        'valid': False,
        'errors': [],
        'warnings': [],
        'info': {}
    }
    
    # 길이 체크
    if len(message) > 128:
        result['warnings'].append(f"메시지 길이가 권장 크기를 초과합니다: {len(message)} > 128")
    
    # 특수 문자 체크
    if '\r' in message or '\t' in message:
        result['warnings'].append("개행 문자나 탭 문자가 포함되어 있습니다")
    
    try:
        # JSON 파싱 시도
        parsed = json.loads(message)
        result['valid'] = True
        result['info']['parsed_data'] = parsed
        result['info']['field_count'] = len(parsed) if isinstance(parsed, dict) else 0
        
        # 필수 필드 체크
        if isinstance(parsed, dict):
            if 'c' not in parsed and 'command' not in parsed:
                result['errors'].append("명령 필드('c' 또는 'command')가 없습니다")
            
            # 권장 필드 형식 체크
            if 'c' in parsed:
                result['info']['optimized_format'] = True
            else:
                result['warnings'].append("최적화된 형식('c')을 사용하지 않습니다")
        else:
            result['errors'].append("JSON이 딕셔너리 형태가 아닙니다")
            
    except json.JSONDecodeError as e:
        result['errors'].append(f"JSON 파싱 실패: {e}")
        
    return result

class ArduinoDebugger:
    """Arduino 통신 디버깅 도구"""
    
    def __init__(self, port='/dev/ttyS0', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.logger = logging.getLogger(__name__)
        
        # 통신 기록
        self.communication_log = []
        
    def connect(self) -> bool:
        """Arduino에 연결"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=5.0
            )
            time.sleep(2)  # 연결 안정화
            print(f"✅ Arduino 연결 성공: {self.port}")
            return True
        except Exception as e:
            print(f"❌ Arduino 연결 실패: {e}")
            return False
    
    def disconnect(self):
        """연결 해제"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("Arduino 연결 해제")
    
    def test_communication(self) -> Dict[str, Any]:
        """기본 통신 테스트"""
        if not self.serial_conn:
            return {'success': False, 'error': '연결되지 않음'}
        
        test_commands = [
            '{"c":"ping"}',
            '{"c":"sensor"}',
            '{"c":"status"}',
        ]
        
        results = []
        
        for cmd in test_commands:
            print(f"\n📤 테스트 명령: {cmd}")
            
            # 메시지 검증
            validation = validate_json_message(cmd)
            print(f"📋 검증 결과: {'✅ 유효' if validation['valid'] else '❌ 무효'}")
            
            if validation['errors']:
                print(f"❌ 오류: {', '.join(validation['errors'])}")
            if validation['warnings']:
                print(f"⚠️ 경고: {', '.join(validation['warnings'])}")
            
            # 명령 전송
            try:
                self.serial_conn.reset_input_buffer()
                
                start_time = time.time()
                self.serial_conn.write((cmd + '\n').encode('utf-8'))
                self.serial_conn.flush()
                
                # 응답 대기
                response = self.serial_conn.readline().decode('utf-8').strip()
                response_time = time.time() - start_time
                
                print(f"📥 응답 ({response_time:.3f}s): {response}")
                
                # 응답 검증
                if response:
                    resp_validation = validate_json_message(response)
                    if resp_validation['valid']:
                        print("✅ 응답 유효")
                    else:
                        print(f"❌ 응답 무효: {resp_validation['errors']}")
                else:
                    print("❌ 응답 없음")
                
                results.append({
                    'command': cmd,
                    'response': response,
                    'response_time': response_time,
                    'success': bool(response),
                    'validation': validation,
                    'response_validation': resp_validation if response else None
                })
                
            except Exception as e:
                print(f"❌ 통신 오류: {e}")
                results.append({
                    'command': cmd,
                    'error': str(e),
                    'success': False
                })
            
            time.sleep(1)  # 명령 간 대기
        
        return {
            'success': True,
            'tests': results,
            'summary': {
                'total': len(test_commands),
                'passed': sum(1 for r in results if r.get('success', False)),
                'failed': sum(1 for r in results if not r.get('success', False))
            }
        }
    
    def interactive_mode(self):
        """대화형 디버깅 모드"""
        print("\n🔧 Arduino 대화형 디버깅 모드")
        print("명령을 입력하세요 (종료: 'quit', 도움말: 'help')")
        
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if user_input.lower() == 'quit':
                    break
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                elif user_input.lower() == 'stats':
                    self._show_stats()
                    continue
                elif user_input.lower().startswith('validate '):
                    message = user_input[9:]
                    validation = validate_json_message(message)
                    self._print_validation_result(validation)
                    continue
                
                # JSON 명령으로 처리
                if not user_input.startswith('{'):
                    # 간단한 명령을 JSON으로 변환
                    user_input = f'{{"c":"{user_input}"}}'
                
                # 검증
                validation = validate_json_message(user_input)
                self._print_validation_result(validation)
                
                if not validation['valid']:
                    continue
                
                # 전송
                self._send_and_receive(user_input)
                
            except KeyboardInterrupt:
                print("\n대화형 모드 종료")
                break
            except Exception as e:
                print(f"❌ 오류: {e}")
    
    def _send_and_receive(self, command: str):
        """명령 전송 및 응답 수신"""
        if not self.serial_conn:
            print("❌ Arduino가 연결되지 않았습니다")
            return
        
        try:
            self.serial_conn.reset_input_buffer()
            
            start_time = time.time()
            self.serial_conn.write((command + '\n').encode('utf-8'))
            self.serial_conn.flush()
            print(f"📤 전송: {command}")
            
            # 응답 대기 (최대 5초)
            response = ""
            for _ in range(50):  # 5초 동안 0.1초씩 대기
                if self.serial_conn.in_waiting:
                    response = self.serial_conn.readline().decode('utf-8').strip()
                    break
                time.sleep(0.1)
            
            response_time = time.time() - start_time
            
            if response:
                print(f"📥 응답 ({response_time:.3f}s): {response}")
                
                # 응답 검증
                validation = validate_json_message(response)
                if validation['valid']:
                    parsed = validation['info']['parsed_data']
                    print(f"✅ 파싱된 응답: {json.dumps(parsed, indent=2, ensure_ascii=False)}")
                else:
                    print(f"⚠️ 응답 파싱 문제: {validation['errors']}")
            else:
                print("❌ 응답 없음 (타임아웃)")
            
            # 통신 기록
            self.communication_log.append({
                'timestamp': time.time(),
                'command': command,
                'response': response,
                'response_time': response_time
            })
            
        except Exception as e:
            print(f"❌ 통신 오류: {e}")
    
    def _print_validation_result(self, validation: Dict[str, Any]):
        """검증 결과 출력"""
        if validation['valid']:
            print("✅ JSON 유효")
            if validation['info']:
                info = validation['info']
                print(f"   📊 필드 수: {info.get('field_count', 0)}")
                if info.get('optimized_format'):
                    print("   ⚡ 최적화된 형식 사용")
        else:
            print("❌ JSON 무효")
        
        if validation['errors']:
            for error in validation['errors']:
                print(f"   ❌ {error}")
        
        if validation['warnings']:
            for warning in validation['warnings']:
                print(f"   ⚠️ {warning}")
    
    def _show_help(self):
        """도움말 표시"""
        print("""
🔧 Arduino 디버깅 도구 도움말

명령어:
  ping          - 연결 테스트
  sensor        - 센서 데이터 요청  
  status        - 시스템 상태 확인
  stepper       - 스테핑 모터 테스트
  servo         - 서보모터 테스트
  clean         - 청소 명령
  reset         - 시스템 리셋
  test          - 하드웨어 테스트
  
특수 명령어:
  help          - 이 도움말 표시
  stats         - 통신 통계 표시
  validate <json> - JSON 메시지 검증
  quit          - 프로그램 종료

JSON 형식:
  {"c":"명령어"}
  {"c":"stepper","s":2048,"sp":12}
  
예제:
  > ping
  > {"c":"sensor"}
  > validate {"c":"test"}
        """)
    
    def _show_stats(self):
        """통신 통계 표시"""
        if not self.communication_log:
            print("📊 통신 기록이 없습니다")
            return
        
        total = len(self.communication_log)
        successful = sum(1 for log in self.communication_log if log['response'])
        avg_time = sum(log['response_time'] for log in self.communication_log) / total
        
        print(f"""
📊 통신 통계:
   총 명령: {total}
   성공: {successful} ({successful/total*100:.1f}%)
   실패: {total-successful} ({(total-successful)/total*100:.1f}%)
   평균 응답 시간: {avg_time:.3f}초
        """)
    
    def save_log(self, filename: str):
        """통신 로그 저장"""
        log_data = {
            'port': self.port,
            'baudrate': self.baudrate,
            'timestamp': time.time(),
            'communication_log': self.communication_log
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        print(f"📁 로그 저장됨: {filename}")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='Arduino JSON 통신 디버깅 도구')
    parser.add_argument('--port', default='/dev/ttyS0', help='시리얼 포트')
    parser.add_argument('--baudrate', type=int, default=115200, help='통신 속도')
    parser.add_argument('--test', action='store_true', help='자동 테스트 실행')
    parser.add_argument('--validate', help='JSON 메시지 검증')
    
    args = parser.parse_args()
    
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    print("🔧 Arduino JSON 통신 디버깅 도구")
    print("=" * 50)
    
    # JSON 검증만 수행
    if args.validate:
        print(f"📋 JSON 검증: {args.validate}")
        validation = validate_json_message(args.validate)
        
        if validation['valid']:
            print("✅ 유효한 JSON")
            parsed = validation['info']['parsed_data']
            print(f"파싱된 데이터: {json.dumps(parsed, indent=2, ensure_ascii=False)}")
        else:
            print("❌ 무효한 JSON")
            for error in validation['errors']:
                print(f"  - {error}")
        
        if validation['warnings']:
            print("\n⚠️ 경고:")
            for warning in validation['warnings']:
                print(f"  - {warning}")
        
        return
    
    # Arduino 디버거 시작
    debugger = ArduinoDebugger(args.port, args.baudrate)
    
    try:
        if not debugger.connect():
            print("❌ Arduino 연결에 실패했습니다")
            return 1
        
        if args.test:
            # 자동 테스트
            print("\n🧪 자동 통신 테스트 시작...")
            results = debugger.test_communication()
            
            print(f"\n📊 테스트 결과:")
            print(f"   총 테스트: {results['summary']['total']}")
            print(f"   성공: {results['summary']['passed']}")
            print(f"   실패: {results['summary']['failed']}")
            
            # 로그 저장
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            log_filename = f"arduino_debug_{timestamp}.json"
            debugger.save_log(log_filename)
        else:
            # 대화형 모드
            debugger.interactive_mode()
    
    except KeyboardInterrupt:
        print("\n프로그램 중단됨")
    finally:
        debugger.disconnect()
    
    return 0

if __name__ == "__main__":
    exit(main()) 