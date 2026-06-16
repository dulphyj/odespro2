export interface PageItem {
  id: string;
  page_number: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  enh_image_path?: string | null;
}

export interface DocumentResponse {
  id: string;
  title: string;
  doc_type: 'pdf' | 'image';
  original_filename: string;
  total_pages: number;
  created_at: string;
  pages: PageItem[];
}

export interface DocumentList {
  id: string;
  title: string;
  doc_type: 'pdf' | 'image';
  original_filename: string;
  total_pages: number;
  created_at: string;
}

export interface PageResponse {
  id: string;
  document_id: string;
  page_number: number;
  status: string;
  orig_image_path?: string | null;
  enh_image_path?: string | null;
  ocr_text?: string | null;
}

export interface PageStatus {
  id: string;
  status: string;
  enh_image_path?: string | null;
}
