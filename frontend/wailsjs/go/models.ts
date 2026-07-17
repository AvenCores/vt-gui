export namespace main {
	
	export class Detection {
	    engine: string;
	    category: string;
	    result: string;
	    method: string;
	
	    static createFrom(source: any = {}) {
	        return new Detection(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.engine = source["engine"];
	        this.category = source["category"];
	        this.result = source["result"];
	        this.method = source["method"];
	    }
	}
	export class ScanResult {
	    hash: string;
	    filename: string;
	    size: number;
	    status: string;
	    stats: Record<string, number>;
	    detections: Detection[];
	    reportUrl: string;
	    message: string;
	
	    static createFrom(source: any = {}) {
	        return new ScanResult(source);
	    }
	
	    constructor(source: any = {}) {
	        if ('string' === typeof source) source = JSON.parse(source);
	        this.hash = source["hash"];
	        this.filename = source["filename"];
	        this.size = source["size"];
	        this.status = source["status"];
	        this.stats = source["stats"];
	        this.detections = this.convertValues(source["detections"], Detection);
	        this.reportUrl = source["reportUrl"];
	        this.message = source["message"];
	    }
	
		convertValues(a: any, classs: any, asMap: boolean = false): any {
		    if (!a) {
		        return a;
		    }
		    if (a.slice && a.map) {
		        return (a as any[]).map(elem => this.convertValues(elem, classs));
		    } else if ("object" === typeof a) {
		        if (asMap) {
		            for (const key of Object.keys(a)) {
		                a[key] = new classs(a[key]);
		            }
		            return a;
		        }
		        return new classs(a);
		    }
		    return a;
		}
	}

}

