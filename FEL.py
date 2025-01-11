'''
this file creates future event list and sort it by time
'''

def create_fel(future_event_list :list,
               clock,
               Patient,
               Event,
               time):
    if Patient is None:
        print(clock, Event, time)
    new_fel = {
        'patient' : Patient,
        'event'   : Event,
        'time'    : clock + time
    }
    future_event_list.append(new_fel)
    return future_event_list

def remove_fel(future_event_list : list):
    future_event_list.pop(0)
    future_event_list.sort(key=lambda x: x['time'])
    return future_event_list

def get_clock(fel):
    first_fel = fel[0]
    clock = first_fel['time']
    return clock