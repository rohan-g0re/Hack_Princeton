'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api-client';
import { JobStatus } from '@/lib/types';

interface JobStatusData {
  status: JobStatus;
  cart_count: number;
  knot_api_count: number;
  message?: string;
}

export function useJobStatus(jobId: string | null) {
  const [data, setData] = useState<JobStatusData | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    if (!jobId) return;
    
    let isMounted = true;
    let timeoutId: NodeJS.Timeout;
    
    async function poll() {
      try {
        const result = await api.getDriverStatus(jobId);
        if (isMounted) {
          setData(result);
          
          // Continue polling if still running
          if (result.status === 'running' || result.status === 'pending') {
            timeoutId = setTimeout(poll, 3000); // Poll every 3s
          }
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message);
        }
      }
    }
    
    poll();
    
    return () => {
      isMounted = false;
      clearTimeout(timeoutId);
    };
  }, [jobId]);
  
  return { data, error };
}

