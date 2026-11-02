export function nextPlayback(index:number, last:number, running:boolean): {index:number;running:boolean} {
  if (index >= last) return {index:-1,running:true};
  return {index,running:!running};
}
