"""Exact 7.0.0-30 isolated candidate, generated numeric bpftrace 0.25 protocol."""

START = 2147483001
STOP = 2147483002


def emit(kind, subject='tid', birth='curtask->start_boottime', first='0', second='0',
         third='0', fourth='0', result='0'):
    fields = ', '.join(map(str, (kind, subject, birth, first, second, third, fourth, result)))
    return f'''if (@active[cpu]) {{
      @hits[cpu, {kind}] = @hits[cpu, {kind}] + 1;
      @sequence[cpu] = @sequence[cpu] + 1;
      printf("E %llu %u %llu %llu %llu %llu %llu %llu %llu %llu %lld\\n",
             nsecs(monotonic), cpu, @sequence[cpu], {fields});
      @attempted[cpu, {kind}] = @attempted[cpu, {kind}] + 1;
    }}'''


def program():
    target = 'pid == $1 && curtask->group_leader->start_boottime / 10000000 == $2'
    disk = '$request != 0 && $request->q->disk->major == $3 && $request->q->disk->first_minor == $6'
    request = '(uint64)$request'
    generation = '@generation[(uint64)$request]'
    retire = emit(16, request, generation) + f' $deleted = delete({generation});'
    allocate = f'''
        @allocation[cpu] = @allocation[cpu] + 1;
        $new = ((uint64)(cpu + 1) << 48) | @allocation[cpu];
        {generation} = $new;
        if ({generation} != $new || (uint64)@allocation[cpu] >= (uint64)281474976710656) {{
          {emit(23, request, '0', '1')}
        }}
        {emit(26, request, generation, '$allocation_type')}
    '''
    parts = ['config = { max_map_keys = 256; perf_rb_pages = 8; missing_probes = "error"; }']
    parts.append('''BEGIN { printf("E %llu %u 0 20 0 0 0 0 0 0 0\\n", nsecs(monotonic), cpu); }''')
    parts.append(f'''tracepoint:syscalls:sys_enter_getpgid /pid == $7/ {{
      if (args.pid == {START} && !@active[cpu]) {{
        @sequence[cpu] = 0; @active[cpu] = 1; {emit(24)}
      }}
      if (args.pid == {STOP} && @active[cpu]) {{ {emit(25)} @active[cpu] = 0; }}
    }}''')
    parts.append(f'''rawtracepoint:sched_switch {{
      $prev = (struct task_struct *)arg1; $next = (struct task_struct *)arg2;
      if ($prev->tgid == $1 && $prev->group_leader->start_boottime / 10000000 == $2) {{
        {emit(1, '$prev->pid', '$prev->start_boottime', 'arg0 || arg3 == 0')}
      }}
      if ($next->tgid == $1 && $next->group_leader->start_boottime / 10000000 == $2) {{
        {emit(3, '$next->pid', '$next->start_boottime')}
      }}
    }}''')
    parts.append(f'''rawtracepoint:sched_wakeup, rawtracepoint:sched_wakeup_new {{
      $task = (struct task_struct *)arg0;
      if ($task->tgid == $1 && $task->group_leader->start_boottime / 10000000 == $2) {{
        {emit(2, '$task->pid', '$task->start_boottime')}
      }}
    }}''')
    for name, kind in (('vmscan:mm_vmscan_direct_reclaim_begin', 4),
                       ('vmscan:mm_vmscan_direct_reclaim_end', 5),
                       ('syscalls:sys_enter_rename', 8), ('sched:sched_process_exit', 19)):
        parts.append(f'tracepoint:{name} /{target}/ {{ {emit(kind)} }}')
    parts.append(f'''tracepoint:syscalls:sys_enter_fsync /{target}/ {{
      @fd[tid] = args.fd; {emit(6, first='args.fd')}
    }}''')
    parts.append(f'''tracepoint:syscalls:sys_exit_fsync /{target}/ {{
      {emit(7, first='@fd[tid]', result='args.ret')} $deleted = delete(@fd[tid]);
    }}''')
    parts.append(f'tracepoint:syscalls:sys_exit_rename /{target}/ {{ {emit(9, result="args.ret")} }}')
    parts.append(f'''tracepoint:syscalls:sys_exit_write /(cgroup == $4 || cgroup == $5) && args.ret > 0/ {{
      {emit(10, first='cgroup', second='args.ret')}
    }}''')
    parts.append(f'''kretprobe:blk_mq_rq_ctx_init.isra.0 {{
      $request = kptr((struct request *)retval);
      if ({disk}) {{
        if ({generation}) {{ {emit(27, request, generation, '1')} }}
        $allocation_type = 0;
        {allocate}
      }}
    }}''')
    parts.append(f'''kprobe:blk_rq_init {{
      $queue = (struct request_queue *)arg0; $request = (struct request *)arg1;
      if ($queue->disk->major == $3 && $queue->disk->first_minor == $6) {{
        if ({generation}) {{
          if (@reset_complete[(uint64)$request] != {generation}) {{
            {emit(27, request, generation, '2')}
          }}
          {emit(16, request, generation, '2')}
        }}
        $allocation_type = 1;
        {allocate}
        @reset[(uint64)$request] = {generation};
        $deleted = delete(@reset_complete[(uint64)$request]);
      }}
    }}''')
    for name, kind in (('insert', 11), ('issue', 12), ('requeue', 13), ('merge', 15)):
        parts.append(f'''rawtracepoint:block_rq_{name} {{
          $request = (struct request *)arg0;
          if ({disk}) {{
            $owner = (uint64)0; $bio = $request->bio;
            if ($bio != 0 && $bio->bi_blkg != 0 && $bio->bi_next == 0) {{
              $owner = $bio->bi_blkg->blkcg->css.cgroup->kn->id;
            }}
            {emit(kind, request, generation, '$request->__data_len', '$request->cmd_flags', '$owner', 'cgroup')}
          }}
        }}''')
    parts.append(f'''kprobe:blk_insert_flush {{
      $request = (struct request *)arg0;
      if ({disk}) {{
        {emit(28, request, generation, '$request->__data_len', '$request->cmd_flags')}
      }}
    }}''')
    parts.append(f'''rawtracepoint:block_rq_complete {{
      $request = (struct request *)arg0;
      if ({disk}) {{
        {emit(14, request, generation, 'arg2', '$request->__data_len', '$request->rq_flags', result='arg1')}
        if (@reset[(uint64)$request] == {generation} && arg2 == $request->__data_len) {{
          @reset_complete[(uint64)$request] = {generation};
        }}
      }}
    }}''')
    parts.append(f'''kprobe:__blk_mq_free_request {{
      $request = (struct request *)arg0;
      if ({disk}) {{ {retire} }}
    }}''')
    parts.append(f'''kprobe:blk_mq_put_tags {{
      $tags = kptr((struct blk_mq_tags *)arg0); $array = kptr((int *)arg1); $count = (uint32)arg2;
      if ($count > 32) {{ {emit(23, first='$count')} }}
      for ($index : 0..32) {{
        if ($index >= $count) {{ break; }}
        $tag = (uint32)*($array + $index);
        $request = $tags->rqs[$tag];
        if ({disk}) {{ {emit(16, request, generation, '1')} $deleted = delete({generation}); }}
      }}
    }}''')
    for name, kind in (('mkdir', 17), ('rmdir', 18)):
        parts.append(f'tracepoint:cgroup:cgroup_{name} {{ {emit(kind, "args.id", "0")} }}')
    parts.append('''END {
      for ($entry : @hits) {
        printf("C %llu %llu %llu %llu\\n", $entry.0.0, $entry.0.1,
               $entry.1, @attempted[$entry.0.0, $entry.0.1]);
      }
      printf("E %llu %u 0 21 0 0 0 0 0 0 0\\n", nsecs(monotonic), cpu);
      clear(@hits); clear(@attempted); clear(@sequence); clear(@active);
      clear(@generation); clear(@allocation); clear(@fd);
      clear(@reset); clear(@reset_complete);
    }''')
    return '\n\n'.join(parts) + '\n'


if __name__ == '__main__':
    print(program(), end='')
