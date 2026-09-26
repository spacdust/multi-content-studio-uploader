import React, { useState, useEffect, useCallback } from 'react';
import { ShoppingBag, Search, Check, RefreshCw, AlertCircle, Trash2, Tag, ChevronRight, Store } from 'lucide-react';
import { searchTikTokProductsApi } from '../../api/contentApi';

export default function TikTokProductCard({
  selectedItem,
  currentEdit,
  setEditedItems,
  selectedAccount,
  showToast,
}) {
  const currentProduct = currentEdit?.tiktokProduct || selectedItem?.meta?.tiktok_product || { enabled: false };
  const isEnabled = Boolean(currentProduct?.enabled);

  const [searchQuery, setSearchQuery] = useState('');
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [isChangingProduct, setIsChangingProduct] = useState(false);

  // Helper to update tiktokProduct in parent edit state
  const updateProductState = useCallback((patch) => {
    setEditedItems((prev) => {
      const currentItemEdit = prev[selectedItem.item_key] || {};
      const existingProduct = currentItemEdit.tiktokProduct || selectedItem?.meta?.tiktok_product || { enabled: false };
      return {
        ...prev,
        [selectedItem.item_key]: {
          ...currentItemEdit,
          tiktokProduct: {
            ...existingProduct,
            ...patch,
          },
        },
      };
    });
  }, [selectedItem, setEditedItems]);

  // Fetch products from TikTok Shop API
  const handleFetchProducts = useCallback(async (query = '') => {
    if (!selectedAccount) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await searchTikTokProductsApi(selectedAccount, query);
      if (res.status === 'success') {
        setProducts(res.products || []);
        setHasSearched(true);
      } else {
        setErrorMsg(res.message || 'Gagal memuat produk dari TikTok Shop');
        setProducts([]);
      }
    } catch (err) {
      setErrorMsg('Gagal terhubung ke API TikTok Shop: ' + err.message);
      setProducts([]);
    } finally {
      setLoading(false);
    }
  }, [selectedAccount]);

  // Auto-fetch products when switch is turned on and no product selected
  useEffect(() => {
    if (isEnabled && !currentProduct?.product_id && products.length === 0 && !hasSearched && !loading) {
      handleFetchProducts('');
    }
  }, [isEnabled, currentProduct?.product_id, products.length, hasSearched, loading, handleFetchProducts]);

  // Toggle switch ON / OFF
  const handleToggle = (checked) => {
    if (checked) {
      updateProductState({
        enabled: true,
      });
      if (products.length === 0) {
        handleFetchProducts(searchQuery);
      }
    } else {
      updateProductState({
        enabled: false,
      });
      setIsChangingProduct(false);
    }
  };

  // Select a product
  const handleSelectProduct = (prod) => {
    const defaultTitle = prod.title ? prod.title.slice(0, 30).trim() : '';
    updateProductState({
      enabled: true,
      product_id: prod.product_id,
      title: prod.title,
      custom_title: currentProduct?.custom_title || defaultTitle,
      format_price: prod.format_price,
      stock_num: prod.stock_num,
      cover_url: prod.cover_url,
    });
    setIsChangingProduct(false);
    if (showToast) {
      showToast(`✓ Produk '${prod.title.slice(0, 25)}...' dipilih`);
    }
  };

  // Remove / clear selected product
  const handleClearSelectedProduct = () => {
    updateProductState({
      product_id: null,
      title: '',
      custom_title: '',
      format_price: '',
      stock_num: 0,
      cover_url: '',
    });
    setIsChangingProduct(true);
  };

  return (
    <div className={`p-3.5 rounded-xl border transition-all ${
      isEnabled
        ? 'bg-amber-950/20 border-amber-500/40 shadow-xs'
        : 'bg-zinc-950/70 border-zinc-800'
    } flex flex-col gap-3`}>
      {/* Header with Switch */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className={`p-1.5 rounded-lg ${
            isEnabled ? 'bg-amber-500/20 text-amber-400' : 'bg-zinc-800 text-zinc-400'
          }`}>
            <ShoppingBag className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-[11px] font-semibold text-zinc-200">
                Keranjang Kuning (Tautan Produk)
              </span>
              <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-amber-950/80 border border-amber-800/60 text-amber-300 font-semibold">
                Khusus TikTok
              </span>
            </div>
            <p className="text-[10px] text-zinc-400">
              {isEnabled ? 'Tautan keranjang kuning aktif' : 'Nonaktif (Tanpa tautan produk)'}
            </p>
          </div>
        </div>

        {/* Toggle Switch */}
        <button
          type="button"
          role="switch"
          aria-checked={isEnabled}
          onClick={() => handleToggle(!isEnabled)}
          className={`relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
            isEnabled ? 'bg-amber-500' : 'bg-zinc-800 hover:bg-zinc-700'
          }`}
        >
          <span
            className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out ${
              isEnabled ? 'translate-x-4' : 'translate-x-0'
            }`}
          />
        </button>
      </div>

      {/* Main Content when Switch is ON */}
      {isEnabled && (
        <div className="flex flex-col gap-3 pt-1 border-t border-zinc-800/80">
          {/* A. If a product is already selected and user is not in "change product" mode */}
          {currentProduct?.product_id && !isChangingProduct ? (
            <div className="flex flex-col gap-2.5">
              {/* Product Preview Card */}
              <div className="flex items-start justify-between gap-3 p-2.5 rounded-xl bg-zinc-900/90 border border-amber-500/30">
                <div className="flex items-start gap-2.5 min-w-0">
                  {currentProduct.cover_url ? (
                    <img
                      src={currentProduct.cover_url}
                      alt={currentProduct.title}
                      className="w-11 h-11 rounded-lg object-cover border border-zinc-700/80 flex-shrink-0 bg-zinc-800"
                    />
                  ) : (
                    <div className="w-11 h-11 rounded-lg bg-zinc-800 flex items-center justify-center flex-shrink-0 text-zinc-500">
                      <ShoppingBag className="w-5 h-5 text-amber-400" />
                    </div>
                  )}

                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-zinc-100 line-clamp-1" title={currentProduct.title}>
                      {currentProduct.title}
                    </p>
                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                      {currentProduct.format_price && (
                        <span className="text-[10px] font-bold text-amber-400 font-mono">
                          {currentProduct.format_price}
                        </span>
                      )}
                      {currentProduct.stock_num !== undefined && (
                        <span className="text-[9px] px-1.5 py-0.2 rounded bg-zinc-800 text-zinc-400 border border-zinc-700">
                          Stok: {currentProduct.stock_num}
                        </span>
                      )}
                      <span className="text-[9px] px-1.5 py-0.2 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-800/60 font-medium">
                        Toko Saya
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-1 flex-shrink-0">
                  <button
                    type="button"
                    onClick={() => {
                      setIsChangingProduct(true);
                      if (products.length === 0) handleFetchProducts('');
                    }}
                    title="Ganti produk lain"
                    className="text-[10px] px-2 py-1 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-lg border border-zinc-700 transition"
                  >
                    Ganti
                  </button>
                  <button
                    type="button"
                    onClick={handleClearSelectedProduct}
                    title="Hapus tautan produk ini"
                    className="p-1 hover:bg-red-950/60 text-zinc-500 hover:text-red-400 rounded-lg transition"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* B. Custom Product Name Input ("Nama Keranjang Kuning") */}
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-[10px] font-semibold text-zinc-300 flex items-center gap-1">
                    <Tag className="w-3 h-3 text-amber-400" />
                    <span>Nama Keranjang Kuning (Tampil di Video):</span>
                  </label>
                  <span className={`text-[10px] font-mono ${
                    (currentProduct.custom_title || '').length > 25 ? 'text-amber-400 font-semibold' : 'text-zinc-500'
                  }`}>
                    {(currentProduct.custom_title || '').length}/30
                  </span>
                </div>

                <div className="relative">
                  <input
                    type="text"
                    maxLength={30}
                    value={currentProduct.custom_title || ''}
                    onChange={(e) => updateProductState({ custom_title: e.target.value })}
                    placeholder="Contoh: WANGI MEWAH, PARFUM VIRAL..."
                    className="w-full bg-zinc-900 border border-zinc-800 px-3 py-1.5 rounded-lg text-xs text-amber-300 font-medium outline-none placeholder:text-zinc-600 focus:border-amber-500/60 transition"
                  />
                </div>
                <p className="text-[9px] text-zinc-500 leading-relaxed">
                  Nama ini yang akan tampil langsung di kartu keranjang kuning video TikTok (Maks. 30 karakter).
                </p>
              </div>
            </div>
          ) : (
            /* C. Product Search & Selection Flow */
            <div className="flex flex-col gap-2.5">
              {isChangingProduct && currentProduct?.product_id && (
                <div className="flex items-center justify-between text-[10px] text-zinc-400 bg-zinc-900/60 px-2.5 py-1.5 rounded-lg border border-zinc-800">
                  <span>Memilih produk pengganti...</span>
                  <button
                    type="button"
                    onClick={() => setIsChangingProduct(false)}
                    className="text-amber-400 hover:underline"
                  >
                    Batal Ganti
                  </button>
                </div>
              )}

              {/* Search Bar */}
              <div className="flex items-center gap-1.5">
                <div className="relative flex-1 min-w-0">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleFetchProducts(searchQuery);
                      }
                    }}
                    placeholder="Cari nama produk toko (misal: Scandalous)..."
                    className="w-full bg-zinc-900 border border-zinc-800 pl-3 pr-8 py-1.5 rounded-lg text-xs text-zinc-200 outline-none placeholder:text-zinc-600 focus:border-amber-500/50"
                  />
                  {searchQuery && (
                    <button
                      type="button"
                      onClick={() => {
                        setSearchQuery('');
                        handleFetchProducts('');
                      }}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 text-xs"
                    >
                      ×
                    </button>
                  )}
                </div>

                {/* Search Button */}
                <button
                  type="button"
                  onClick={() => handleFetchProducts(searchQuery)}
                  disabled={loading}
                  title="Cari Produk"
                  className="px-2.5 py-1.5 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 rounded-lg text-xs font-semibold flex items-center gap-1 transition disabled:opacity-50"
                >
                  {loading ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Search className="w-3.5 h-3.5" />
                  )}
                  <span>Cari</span>
                </button>

                {/* Refresh all */}
                <button
                  type="button"
                  onClick={() => {
                    setSearchQuery('');
                    handleFetchProducts('');
                  }}
                  disabled={loading}
                  title="Muat Ulang Seluruh Produk Toko"
                  className="p-1.5 bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 border border-zinc-800 rounded-lg transition disabled:opacity-50"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                </button>
              </div>

              {/* Error Message */}
              {errorMsg && (
                <div className="p-2.5 rounded-lg bg-red-950/40 border border-red-800/40 flex items-start gap-2">
                  <AlertCircle className="w-3.5 h-3.5 text-red-400 flex-shrink-0 mt-0.5" />
                  <p className="text-[10px] text-red-300 leading-relaxed">{errorMsg}</p>
                </div>
              )}

              {/* Loading State */}
              {loading && (
                <div className="py-6 text-center text-zinc-500 text-xs flex flex-col items-center gap-1.5">
                  <RefreshCw className="w-4 h-4 animate-spin text-amber-400" />
                  <span>Memuat daftar produk dari TikTok Shop...</span>
                </div>
              )}

              {/* Products List */}
              {!loading && products.length > 0 && (
                <div className="flex flex-col gap-1.5 max-h-48 overflow-y-auto custom-scrollbar pr-0.5">
                  {products.map((prod) => {
                    const isSelected = currentProduct?.product_id === prod.product_id;
                    return (
                      <div
                        key={prod.product_id}
                        onClick={() => handleSelectProduct(prod)}
                        className={`flex items-center justify-between gap-2.5 p-2 rounded-lg border cursor-pointer transition ${
                          isSelected
                            ? 'bg-amber-950/40 border-amber-500/60 shadow-xs'
                            : 'bg-zinc-900/60 hover:bg-zinc-900 border-zinc-800/80 hover:border-zinc-700'
                        }`}
                      >
                        <div className="flex items-center gap-2 min-w-0">
                          {/* Radio Circle */}
                          <div className={`w-3.5 h-3.5 rounded-full border flex items-center justify-center flex-shrink-0 ${
                            isSelected
                              ? 'border-amber-400 bg-amber-500'
                              : 'border-zinc-600 bg-zinc-950'
                          }`}>
                            {isSelected && <div className="w-1.5 h-1.5 rounded-full bg-black" />}
                          </div>

                          {/* Thumbnail */}
                          {prod.cover_url ? (
                            <img
                              src={prod.cover_url}
                              alt={prod.title}
                              className="w-8 h-8 rounded-md object-cover border border-zinc-800 flex-shrink-0 bg-zinc-950"
                            />
                          ) : (
                            <div className="w-8 h-8 rounded-md bg-zinc-800 flex items-center justify-center flex-shrink-0 text-zinc-500">
                              <ShoppingBag className="w-3.5 h-3.5" />
                            </div>
                          )}

                          {/* Title & Info */}
                          <div className="min-w-0">
                            <p className="text-[11px] font-medium text-zinc-200 line-clamp-1" title={prod.title}>
                              {prod.title}
                            </p>
                            <div className="flex items-center gap-1.5 text-[9px]">
                              <span className="font-bold text-amber-400 font-mono">
                                {prod.format_price}
                              </span>
                              {prod.stock_num !== undefined && (
                                <span className="text-zinc-500">
                                  • Stok: {prod.stock_num}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>

                        <div className="flex-shrink-0">
                          <button
                            type="button"
                            className={`text-[10px] font-semibold px-2 py-0.5 rounded-md transition ${
                              isSelected
                                ? 'bg-amber-500 text-black'
                                : 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700'
                            }`}
                          >
                            {isSelected ? 'Terpilih' : 'Pilih'}
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Empty Results State */}
              {!loading && hasSearched && products.length === 0 && !errorMsg && (
                <div className="py-4 text-center text-zinc-500 text-[11px] bg-zinc-900/40 rounded-lg border border-zinc-800/60">
                  Tidak ada produk yang cocok dengan pencarian "{searchQuery}".
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
