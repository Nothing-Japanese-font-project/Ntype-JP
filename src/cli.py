import argparse
import time
import datetime
import os
from processor import FontProcessor
from metadata import MetadataManager

def main():
    parser = argparse.ArgumentParser(description="Process UFO font with NType-JP style.")
    parser.add_argument("--input", required=True, help="Input UFO directory")
    parser.add_argument("--output", help="Output OTF file")
    parser.add_argument("--name", default="NType JP alpha", help="Font family name")
    parser.add_argument("--weight", default="SemiBold", help="Font style name")
    parser.add_argument("--round-size", type=int, default=20, help="Corner rounding size")
    parser.add_argument("--no-parallel", action="store_true", help="Disable parallel processing")
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 1) // 2), help="Number of worker processes (default: half of cores)")
    parser.add_argument("--no-optimize", action="store_true", help="Disable CFF optimization/compression")
    
    args = parser.parse_args()

    processor = FontProcessor(args.input, round_size=args.round_size)
    processor.load()
    
    MetadataManager.update(
        processor.font, 
        args.name, 
        args.weight, 
        "Nothing Japanese Font Project", 
        "NTYP"
    )

    start_time = time.time()
    processor.process(use_parallel=not args.no_parallel, max_workers=args.workers)
    
    now_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    if not args.output:
        args.output = f"dist/NTypeJP-{args.weight}-{now_str}.otf"
    else:
        base, ext = os.path.splitext(args.output)
        args.output = f"{base}_{now_str}{ext}"
    
    out_dir = os.path.dirname(args.output)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    processor.save_otf(args.output, optimize_cff=not args.no_optimize)
    
    duration = time.time() - start_time
    print(f"[{datetime.datetime.now()}] Total duration: {duration:.2f} seconds.")

if __name__ == "__main__":
    main()
